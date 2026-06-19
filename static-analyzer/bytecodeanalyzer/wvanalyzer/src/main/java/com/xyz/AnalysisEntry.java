package com.xyz;

import com.xyz.utils.SootUtils;
import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import sootup.apk.frontend.ApkAnalysisInputLocation;
import sootup.apk.frontend.DexBodyInterceptors;
import sootup.core.inputlocation.AnalysisInputLocation;
import sootup.core.jimple.common.expr.AbstractInvokeExpr;
import sootup.core.jimple.common.stmt.Stmt;
import sootup.core.model.Body;
import sootup.core.model.SootClass;
import sootup.core.model.SootMethod;
import sootup.core.signatures.MethodSignature;
import sootup.core.types.ClassType;
import sootup.java.core.types.JavaClassType;
import sootup.java.core.views.JavaView;

import java.io.File;
import java.io.FileWriter;
import java.io.Writer;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

public class AnalysisEntry {
    String appPath;
    String packageName;
    String outDirectory;

    HashMap<String, Set<SootMethod>> overwrittenMethodsOfInterest = new HashMap<>();

    Set<String> overwriteMethodsOfInterest = new HashSet<>();
    List<SSLOverwriteResult> sslOverwriteMethods = new ArrayList<>();

    public AnalysisEntry(String appPath, String packageName, String outDirectory) {
        this.appPath = appPath;
        this.packageName = packageName;
        this.outDirectory = outDirectory;

        this.overwriteMethodsOfInterest.add("onReceivedSslError");
        this.overwriteMethodsOfInterest.add("onSafeBrowsingHit");
        this.overwriteMethodsOfInterest.add("shouldOverrideUrlLoading");
        this.overwriteMethodsOfInterest.add("shouldInterceptRequest");
        for (String methodName : this.overwriteMethodsOfInterest) {
            this.overwrittenMethodsOfInterest.put(methodName, new HashSet<>());
        }
    }

    public void startAnalysis() {
        AnalysisInputLocation inputLocation = new ApkAnalysisInputLocation(
                Path.of(appPath),
                "",
                DexBodyInterceptors.Default.bodyInterceptors()
        );

        JavaView view = new JavaView(inputLocation);

        JavaClassType webViewType = view.getIdentifierFactory().getClassType("android.webkit.WebView");
        JavaClassType webViewClientType = view.getIdentifierFactory().getClassType("android.webkit.WebViewClient");
        JavaClassType webChromeClientType = view.getIdentifierFactory().getClassType("android.webkit.WebChromeClient");
        JavaClassType webSettingsType = view.getIdentifierFactory().getClassType("android.webkit.WebSettings");

        SootClass superWebViewClass = view.getClassOrThrow(webViewType);
        SootClass superWebViewClientClass = view.getClassOrThrow(webViewClientType);
        SootClass superWebChromeClientClass = view.getClassOrThrow(webChromeClientType);
        SootClass superWebSettingsClass = view.getClassOrThrow(webSettingsType);

        ArrayList<SootClass> webViewClasses = new ArrayList<>();
        ArrayList<SootClass> webViewClientClasses = new ArrayList<>();
        ArrayList<SootClass> webChromeClientClasses = new ArrayList<>();
        ArrayList<SootClass> webSettingsClasses = new ArrayList<>();

        // loop through all classes and all methods in the APK
        view.getClasses().forEach(javaSootClass -> {

            if (!javaSootClass.isApplicationClass()) {
                return;
            }

            if (SootUtils.isClassSubclass(view, javaSootClass, superWebViewClass)) {
                webViewClasses.add(javaSootClass);
            }
            if (SootUtils.isClassSubclass(view, javaSootClass, superWebViewClientClass)) {
                webViewClientClasses.add(javaSootClass);
            }
            if (SootUtils.isClassSubclass(view, javaSootClass, superWebChromeClientClass)) {
                webChromeClientClasses.add(javaSootClass);
            }
            if (SootUtils.isClassSubclass(view, javaSootClass, superWebSettingsClass)) {
                webSettingsClasses.add(javaSootClass);
            }
        });

        // loop through all WebViewClient classes

        webViewClientClasses.forEach(webViewClientClass -> {
            if (!webViewClientClass.isApplicationClass()) {
                return;
            }
            try {
                webViewClientClass.getMethods().forEach(method -> {
                    String methodName = method.getName();
                    if (this.overwriteMethodsOfInterest.contains(methodName)) {
                        this.overwrittenMethodsOfInterest.get(methodName).add(method);
                    }
                    if (methodName.equals("onReceivedSslError")) {
                        SSLErrorOverwriteAnalyzer analyzer = new SSLErrorOverwriteAnalyzer(method);
                        SSLOverwriteResult overwriteResult = analyzer.analyze();
                        this.sslOverwriteMethods.add(overwriteResult);
                    }
                });
            } catch (Exception e) {
                System.err.println("Error processing class " + webViewClientClass.getName() + ": " + e.getMessage());
            }
        });

        List<SootClass> allWebViewRelatedClasses = new ArrayList<>();
        allWebViewRelatedClasses.addAll(webViewClasses);
        allWebViewRelatedClasses.addAll(webViewClientClasses);
        allWebViewRelatedClasses.addAll(webChromeClientClasses);
        allWebViewRelatedClasses.addAll(webSettingsClasses);
        allWebViewRelatedClasses.add(superWebViewClass);
        allWebViewRelatedClasses.add(superWebViewClientClass);
        allWebViewRelatedClasses.add(superWebChromeClientClass);
        allWebViewRelatedClasses.add(superWebSettingsClass);

        List<CallLocation> webViewRelatedCallLocation = findWebViewCalls(view, allWebViewRelatedClasses);


        // set mixed content mode
        HashMap<CallLocation, List<ArgumentValue>> mcContentLocationValues = new HashMap<>();

        for (CallLocation location : webViewRelatedCallLocation) {
            Stmt stmt = location.getStmt();
            String tgtMethod = stmt.asInvokableStmt().getInvokeExpr().get().getMethodSignature().getName();
            if (tgtMethod.equals("setMixedContentMode")) {
                ParameterResolver parameterResolver = new ParameterResolver(view);
                Set<ArgumentValue> argValues = parameterResolver.getParameterValue(location, 0);
                mcContentLocationValues.put(location, new ArrayList<>(argValues));
            }
        }

        // write some information to a JSON file
        JsonObject jsonObject = new JsonObject();
        jsonObject.addProperty("packageName", packageName);
        // json array of the webview classes
        JsonArray webviewClassesArray = new JsonArray();
        for (SootClass clazz : webViewClasses) {
            webviewClassesArray.add(clazz.getName());
        }
        jsonObject.add("webviewClasses", webviewClassesArray);
        JsonArray webviewClientClassesArray = new JsonArray();
        for (SootClass clazz : webViewClientClasses) {
            webviewClientClassesArray.add(clazz.getName());
        }
        jsonObject.add("webViewClientClasses", webviewClientClassesArray);
        JsonArray webviewChromeClientClassesArray = new JsonArray();
        for (SootClass clazz : webChromeClientClasses) {
            webviewChromeClientClassesArray.add(clazz.getName());
        }
        jsonObject.add("webChromeClientClasses", webviewChromeClientClassesArray);
        JsonArray webviewSettingsClassesArray = new JsonArray();
        for (SootClass clazz : webSettingsClasses) {
            webviewSettingsClassesArray.add(clazz.getName());
        }
        jsonObject.add("webSettingsClasses", webviewSettingsClassesArray);
        JsonArray webviewRelatedMethodCallsArray = new JsonArray();
        for (CallLocation location : webViewRelatedCallLocation) {
            JsonObject callObject = new JsonObject();
            callObject.addProperty("signature", location.getMethod().getSignature().toString());
            callObject.addProperty("method", location.getMethod().getSignature().getName());
            callObject.addProperty("class", location.getMethod().getDeclClassType().getFullyQualifiedName());
            callObject.addProperty("targetStmt", location.getStmt().toString());
            // get the targert method of the statement
            AbstractInvokeExpr invokeExpr = location.getStmt().asInvokableStmt().getInvokeExpr().orElseThrow();
            MethodSignature targetMethod = invokeExpr.getMethodSignature();
            callObject.addProperty("targetMethodSignature", targetMethod.toString());
            webviewRelatedMethodCallsArray.add(callObject);
        }
        jsonObject.add("webViewRelatedMethods", webviewRelatedMethodCallsArray);
        JsonArray mcContentArray = new JsonArray();
        for (Map.Entry<CallLocation, List<ArgumentValue>> entry : mcContentLocationValues.entrySet()) {
            CallLocation location = entry.getKey();
            List<ArgumentValue> values = entry.getValue();
            JsonObject mcObject = new JsonObject();
            mcObject.addProperty("signature", location.getMethod().getSignature().toString());
            mcObject.addProperty("method", location.getMethod().getName());
            mcObject.addProperty("class", location.getMethod().getDeclClassType().getFullyQualifiedName());
            JsonArray valuesArray = new JsonArray();
            for (ArgumentValue value : values) {
                JsonObject valueObject = new JsonObject();
                valueObject.addProperty("source", value.getSource());
                if (value.getValue() != null) {
                    valueObject.addProperty("value", (Integer)(value.getValue()));
                } else {
                    valueObject.add("value", null);
                }
                valuesArray.add(valueObject);
            }
            mcObject.add("values", valuesArray);
            mcContentArray.add(mcObject);
        }
        jsonObject.add("mixedContentModeSettings", mcContentArray);

        Path out = Paths.get(this.outDirectory, packageName);
        // create the out directory if it does not exist
        File outDir = out.toFile();
        if (!outDir.exists()) {
            boolean created = outDir.mkdirs();
            if (!created) {
                throw new RuntimeException("Could not create output directory: " + outDir.getAbsolutePath());
            }
        }

        // overwritten methods of interest
        JsonObject overwrittenMethodsObject = new JsonObject();
        HashMap<String, String> methodToUuid = new HashMap<>();
        for (Map.Entry<String, Set<SootMethod>> entry : this.overwrittenMethodsOfInterest.entrySet()) {
            String methodName = entry.getKey();
            Set<SootMethod> methods = entry.getValue();
            JsonArray methodsArray = new JsonArray();
            for (SootMethod method : methods) {
                JsonObject methodObject = new JsonObject();
                methodObject.addProperty("signature", method.getSignature().toString());
                methodObject.addProperty("class", method.getSignature().getDeclClassType().getFullyQualifiedName());
                methodObject.addProperty("name", method.getName());
                // get a short uuid
                String uuid = method.getName() + UUID
                        .randomUUID()
                        .toString()
                        .substring(0, 8);
                // create a UUID for the method so we can map it later
                methodObject.addProperty("uuid", uuid);
                // write the uuid and the body to a file with the name of uuid
                Body body = method.getBody();
                String methodBody = body.toString();
                String methodUuid = methodObject.get("uuid").getAsString();
                methodToUuid.put(method.getSignature().toString(), methodUuid);
                String methodOutFile = Paths.get(this.outDirectory, packageName, methodUuid + ".jimple").toString();
                try (Writer writer = new FileWriter(methodOutFile)) {
                    writer.write(methodBody);
                } catch (Exception e) {
                    e.printStackTrace();
                }
                methodsArray.add(methodObject);
            }
            overwrittenMethodsObject.add(methodName, methodsArray);
        }
        jsonObject.add("overwrittenMethodsOfInterest", overwrittenMethodsObject);

        // ssl overwrite methods
        JsonArray sslOverwriteMethodsArray = new JsonArray();
        for (SSLOverwriteResult result : this.sslOverwriteMethods) {
            JsonObject sslObject = new JsonObject();
            sslObject.addProperty("class", result.getSootMethod().getSignature().getDeclClassType().getFullyQualifiedName());
            sslObject.addProperty("method", result.getSootMethod().getSignature().getName());
            sslObject.addProperty("signature", result.getSootMethod().getSignature().toString());
            sslObject.addProperty("containsProceedCall", result.isContainsProceedCall());
            sslObject.addProperty("containsProceedCallString", result.isContainsProceedCallString());
            sslObject.addProperty("callAlwaysReachable", result.isCallAlwaysReachable());
            sslObject.addProperty("uuid", methodToUuid.get(result.getSootMethod().getSignature().toString()));
            sslOverwriteMethodsArray.add(sslObject);
        }
        jsonObject.add("sslOverwriteMethods", sslOverwriteMethodsArray);

        writeResult(packageName, jsonObject);

        // print the

    }

    private void writeResult(String packageName, JsonObject jsonObject) {
        Path out = Paths.get(this.outDirectory, packageName);
        // create the out directory if it does not exist
        File outDir = out.toFile();
        if (!outDir.exists()) {
            boolean created = outDir.mkdirs();
            if (!created) {
                throw new RuntimeException("Could not create output directory: " + outDir.getAbsolutePath());
            }
        }

        String overviewOutputFile = Paths.get(out.toString(), packageName + ".json").toString();
        // write json file
        try (Writer writer = new FileWriter(overviewOutputFile)) {
            Gson gson = new Gson();
            // pretty print
            gson = new Gson().newBuilder().setPrettyPrinting().create();
            gson.toJson(jsonObject, writer);
            System.out.println("Wrote output to " + overviewOutputFile);
        } catch (Exception e) {
            e.printStackTrace();
        }

    }

    private static boolean callsProceed(SootMethod sootMethod) {
        if (!sootMethod.hasBody()) {
            return false;
        }
        return sootMethod.getBody().getStmts().stream().anyMatch(stmt -> {
            if (stmt.isInvokableStmt()) {
                Optional<AbstractInvokeExpr> invokeExprOpt = stmt.asInvokableStmt().getInvokeExpr();
                if (invokeExprOpt.isEmpty()) {
                    return false;
                }
                AbstractInvokeExpr invokeExpr = invokeExprOpt.get();
                MethodSignature methodSignature = invokeExpr.getMethodSignature();
                if (methodSignature.getName().equals("proceed")) {
                    return true;
                }
            }
            return false;
        });
    }


    private static List<CallLocation> findWebViewCalls(JavaView view, List<SootClass> classes) {
        ArrayList<CallLocation> webViewCalls = new ArrayList<>();
        ArrayList<ClassType> classTypes = new ArrayList<>();
        for (SootClass clazz : classes) {
            classTypes.add(clazz.getType());
        }

        view.getClasses().forEach(clazz -> {
            try {
                if (!clazz.isApplicationClass()) {
                    return;
                }
                if (clazz.getName().startsWith("java.") || clazz.getName().startsWith("javax.") || clazz.getName().startsWith("android.") || clazz.getName().startsWith("dalvik.")) {
                    return;
                }
                clazz.getMethods().forEach(method -> {


                    if (!method.hasBody()) {
                        return;
                    }
                    method.getBody().getStmts().forEach(stmt -> {
                        if (stmt.isInvokableStmt()) {
                            Optional<AbstractInvokeExpr> invokeExprOpt = stmt.asInvokableStmt().getInvokeExpr();
                            if (invokeExprOpt.isEmpty()) {
                                return;
                            }
                            AbstractInvokeExpr invokeExpr = invokeExprOpt.get();
                            MethodSignature methodSignature = invokeExpr.getMethodSignature();
                            if (classTypes.contains(methodSignature.getDeclClassType())) {
                                webViewCalls.add(new CallLocation(method, stmt));
                            }
                        }
                    });
                });
            } catch (Exception e) {
                System.err.println("Error processing class " + clazz.getName() + ": " + e.getMessage());
            }
        });
        return webViewCalls;

    }
}
