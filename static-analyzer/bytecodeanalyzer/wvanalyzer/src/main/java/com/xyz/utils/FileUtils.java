package com.xyz.utils;

import java.io.File;
import java.util.Arrays;
import java.util.Comparator;

public class FileUtils {

    public static String getCorrectApkPath(String app) {
        File file = new File(app);
        if (file.exists() && file.isFile()) {
            return app;
        } else if (file.exists() && file.isDirectory()) {
            // retrieve the files in the file
            File[] files = file.listFiles((dir, name) -> name.endsWith(".apk"));
            // get the shortest file name
            if (files == null || files.length == 0) {
                throw new RuntimeException("No apk files found in directory: " + app);
            }
            File[] apks = Arrays.stream(files).sorted(Comparator.comparingInt(file2 -> file2.getName().length())).toArray(File[]::new);
            return apks[0].getAbsolutePath();
        } else {
            throw new RuntimeException("File or directory does not exist: " + app);
        }
    }

    public static String getPackageName(String apkPath) {
        File file = new File(apkPath);
        String packageName = file.getName();
        if (packageName.endsWith(".apk")) {
            packageName = packageName.substring(0, packageName.length() - ".apk".length());
            return packageName;
        } else {
            throw new RuntimeException("File is not an apk: " + apkPath);
        }
    }
}
