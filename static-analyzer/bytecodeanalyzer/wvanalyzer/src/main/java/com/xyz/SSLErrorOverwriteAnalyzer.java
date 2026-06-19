package com.xyz;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import sootup.codepropertygraph.ast.AstCreator;
import sootup.codepropertygraph.cdg.CdgCreator;
import sootup.codepropertygraph.cfg.CfgCreator;
import sootup.codepropertygraph.cpg.CpgCreator;
import sootup.codepropertygraph.ddg.DdgCreator;
import sootup.codepropertygraph.propertygraph.PropertyGraph;
import sootup.codepropertygraph.propertygraph.edges.*;
import sootup.core.graph.StmtGraph;
import sootup.core.jimple.basic.Local;
import sootup.core.jimple.basic.Value;
import sootup.core.jimple.common.constant.IntConstant;
import sootup.core.jimple.common.expr.AbstractInvokeExpr;
import sootup.core.jimple.common.expr.JEqExpr;
import sootup.core.jimple.common.ref.JParameterRef;
import sootup.core.jimple.common.stmt.BranchingStmt;
import sootup.core.jimple.common.stmt.JIfStmt;
import sootup.core.jimple.common.stmt.Stmt;
import sootup.core.model.SootMethod;
import sootup.core.signatures.MethodSignature;

import java.util.*;
import java.util.stream.Collectors;

public class SSLErrorOverwriteAnalyzer {

    private static final Logger logger = LogManager.getLogger(SSLErrorOverwriteAnalyzer.class);

    final String PROCEED_SIGNATURE = "<android.webkit.SslErrorHandler: void proceed()>";
    final String ON_RECEIVED_SSL_ERROR_SIGNATURE = "<android.webkit.WebViewClient: void onReceivedSslError(android.webkit.WebView,android.webkit.SslErrorHandler,android.net.http.SslError)>";

    SootMethod sootMethod;

    public SSLErrorOverwriteAnalyzer(SootMethod sootMethod) {
        this.sootMethod = sootMethod;
    }

    public SSLOverwriteResult analyze() {
        System.out.println("Analyzing method: " + sootMethod.getSignature());
        if (!sootMethod.hasBody()) {
            logger.info("Method {} has no body, skipping analysis.", sootMethod.getSignature());
            throw new RuntimeException("Could not analyze SSL Overwrite. Method " + sootMethod.getSignature() + " has no body");
        }

        SSLOverwriteResult result = new SSLOverwriteResult();
        result.setSootMethod(sootMethod);

        AstCreator astCreator = new AstCreator();
        CfgCreator cfgCreator = new CfgCreator();
        CdgCreator cdgCreator = new CdgCreator();
        DdgCreator ddgCreator = new DdgCreator();
        CpgCreator cpgCreator = new CpgCreator(astCreator, cfgCreator, cdgCreator, ddgCreator);
        PropertyGraph cpg = cpgCreator.createCpg(sootMethod);
        System.out.println(cpg.toDotGraph());

        boolean containsProceedString = sootMethod.getBody().toString().contains("proceed");
        result.setContainsProceedCallString(containsProceedString);

        StmtGraph<?> stmtGraph = sootMethod.getBody().getStmtGraph();
        List<Stmt> proceedCalls = findProceedCalls(stmtGraph);

        if (proceedCalls.isEmpty()) {
            // no proceed calls could be found, so we return
            result.setContainsProceedCall(false);
            return result;
        }
        result.setContainsProceedCall(true);

        ParameterNullCheckAnalysis parameterNullCheckAnalysis = new ParameterNullCheckAnalysis(stmtGraph);

        for (Stmt proceedCall : proceedCalls) {

            ArrayList<ArrayList<Stmt>> paths = getPaths(stmtGraph, proceedCall);
            if (paths.isEmpty()) {
                // this should never happen
                throw new RuntimeException("Could not find any path to proceed() call in method " + sootMethod.getSignature());
            }

            boolean alwaysReachable = true;

            for (List<Stmt> path : paths) {
                boolean containsCallToSuper = containsCallToSuper(new ArrayList<>(path));
                if (containsCallToSuper) {
                    alwaysReachable = false;
                    break;
                }
                ArrayList<Stmt> conditionalStmts = path.stream().filter(stmt -> stmt instanceof BranchingStmt).collect(Collectors.toCollection(ArrayList::new));

                if (conditionalStmts.isEmpty()) {
                    // there are no conditional statements on this path, so proceed() is reachable in this path
                    break;
                } else {
                    for (Stmt conditionalStmt : conditionalStmts) {
                        boolean isNull = checkParameterNullCheckDependency(parameterNullCheckAnalysis, conditionalStmt);
                        if (!isNull) {
                            alwaysReachable = false;
                            break;
                        }
                    }
                }
            }
            result.setCallAlwaysReachable(alwaysReachable);
        }
        return result;
    }

    private boolean containsCallToSuper(ArrayList<Stmt> stmt) {
        for (Stmt s : stmt) {
            if (!s.isInvokableStmt()) {
                continue;
            }
            Optional<AbstractInvokeExpr> optionalAbstractInvokeExpr = s.asInvokableStmt().getInvokeExpr();

            if (optionalAbstractInvokeExpr.isEmpty()) {
                // this is not an invoke statement so we are not interested in it
                continue;
            }

            AbstractInvokeExpr invokeExpr = optionalAbstractInvokeExpr.get();
            MethodSignature calledMethodSignature = invokeExpr.getMethodSignature();

            if (calledMethodSignature.toString().equals(ON_RECEIVED_SSL_ERROR_SIGNATURE)) {
                return true;
            }
        }
        return false;
    }


    private ArrayList<ArrayList<Stmt>> getPaths(StmtGraph<?> stmtGraph, Stmt endStmt) {
        Stmt entryStmt = stmtGraph.getStartingStmt();

        List<Stmt> entries = stmtGraph.predecessors(endStmt);

        ArrayList<ArrayList<Stmt>> result = new ArrayList<>();
        Queue<ArrayList<Stmt>> queue = new ArrayDeque<>();
        for (Stmt entry : entries) {
            ArrayList<Stmt> path = new ArrayList<>();
            path.add(entry);
            queue.add(path);
        }

        while (!queue.isEmpty()) {
            ArrayList<Stmt> path = new ArrayList<>(queue.poll());
            Stmt lastStmt = path.get(0);

            boolean reachedStart = true;
            for (Stmt pred : stmtGraph.predecessors(lastStmt)) {
                if (path.contains(pred)) {
                    // we found a cycle, so we skip this edge
                    continue;
                }
                ArrayList<Stmt> newPath = new ArrayList<>(path);
                newPath.add(0, pred);
                if (pred.equals(entryStmt)) {
                    result.add(newPath);
                    continue;
                }
                queue.add(newPath);
            }

        }
        return result;
    }

    private boolean checkParameterNullCheckDependency(ParameterNullCheckAnalysis parameterNullCheckAnalysis, Stmt stmt) {
        // check if this is just a check if the input parameter is null or not

        if (!(stmt instanceof BranchingStmt)) {
            throw new RuntimeException("The statement is not a branching statement!: " + stmt);
        }

        if (!(stmt instanceof JIfStmt)) {
            throw new RuntimeException("The branching statement is not an if statement!: " + stmt);
        }

        JIfStmt jIfStmt = (JIfStmt) stmt;
        Value condition = jIfStmt.getCondition();

        Map<Local, Set<Value>> flowSet = parameterNullCheckAnalysis.getFlowBefore(stmt);


        if (condition instanceof JEqExpr) {
            JEqExpr jEqExpr = (JEqExpr) condition;
            Value op1 = jEqExpr.getOp1();
            Value op2 = jEqExpr.getOp2();


            boolean rightIsNull = false;
            if (op2 instanceof IntConstant) {
                IntConstant intConstant = (IntConstant) op2;
                if (intConstant.getValue() == 0) {
                    rightIsNull = true;
                }
            }

            if (rightIsNull) {
                // if all values of op1 are of type JParameterRef AND the parameter is of type 'android.webkit.SslErrorHandler', we are fine
                if (op1 instanceof Local) {
                    Local local = (Local) op1;
                    Set<Value> values = flowSet.get(local);
                    if (values != null) {
                        if (values.isEmpty()) {
                            return false;
                        }
                        // check if something holds for all elements
                        return values.stream().allMatch(v -> v instanceof JParameterRef && v.getType().toString().equals("android.webkit.SslErrorHandler"));
                    }
                }

            }

        }


        System.out.println("a");

        /*if (stmt instanceof BranchingStmt) {
            if (stmt instanceof JIfStmt) {
                JIfStmt jIfStmt = (JIfStmt) stmt;
                Value condition = jIfStmt.getCondition();
            }

        } else {
            throw new RuntimeException("The statement is not a branching statement!: " + stmt);
        }



        Map<Local, Set<Value>> in = parameterNullCheckAnalysis.getFlowBefore(stmt);*/
        return false;

    }


    private List<Stmt> findProceedCalls(StmtGraph<?> stmtGraph) {
        logger.info("Finding proceed() calls in method: {}", sootMethod.getSignature());
        List<Stmt> proceedCalls = new java.util.ArrayList<>();


        for (Stmt stmt : stmtGraph.getStmts()) {
            if (!stmt.isInvokableStmt()) {
                continue;
            }
            Optional<AbstractInvokeExpr> optionalAbstractInvokeExpr = stmt.asInvokableStmt().getInvokeExpr();

            if (optionalAbstractInvokeExpr.isEmpty()) {
                // this is not an invoke statement so we are not interested in it
                continue;
            }

            AbstractInvokeExpr invokeExpr = optionalAbstractInvokeExpr.get();
            MethodSignature calledMethodSignature = invokeExpr.getMethodSignature();

            // We find calls to proceed() directly
            if (calledMethodSignature.toString().equals(PROCEED_SIGNATURE)) {
                System.out.println("proceed found");
                proceedCalls.add(stmt);
            }

        }

        // Experimental evaluation has shown that apps may obfuscate the call to proceed() by using reflection.
        // We therefore also look for calls to java.lang.reflect.Method.invoke() where the method name is "proceed".
        // We cannot simply look for calls to "java.lang.reflect", as apps may also use other reflection methods (that they implemented themselves)
        // So we look for calls that have a parameter with the value "proceed".
        // TODO: we have to evaluate how well this approach actually works



        return proceedCalls;
    }


}
