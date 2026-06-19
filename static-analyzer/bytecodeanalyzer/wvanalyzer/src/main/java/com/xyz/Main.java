package com.xyz;

import com.xyz.utils.FileUtils;
import org.apache.commons.cli.*;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;


public class Main {

    private static Logger logger = LogManager.getLogger(Main.class);

    public static void main(String[] args) {

        Options options = new Options();

        Option app = new Option("a", "app", true, "Path to the app file or folder");
        app.setRequired(true);

        Option out = new Option("o", "out", true, "Path to the output folder");
        out.setRequired(true);

        options.addOption(app)
                .addOption(out);

        CommandLineParser commandLineParser = new DefaultParser();
        CommandLine commandLine;

        try {
            commandLine = commandLineParser.parse(options, args);
        } catch (ParseException e) {
            logger.error("Error parsing command line arguments: {}", e.getMessage());
            throw new RuntimeException(e);
        }

        String appPath = commandLine.getOptionValue("app");
        String outDir = commandLine.getOptionValue("out");

        String apkPath = FileUtils.getCorrectApkPath(appPath);

        String packageName = FileUtils.getPackageName(apkPath);

        AnalysisEntry entry = new AnalysisEntry(apkPath, packageName, outDir);
        logger.info("Starting analysis for app: {} ({})", packageName, apkPath);
        entry.startAnalysis();
        logger.info("Analysis finished for app: {} ({})", packageName, apkPath);
    }


}