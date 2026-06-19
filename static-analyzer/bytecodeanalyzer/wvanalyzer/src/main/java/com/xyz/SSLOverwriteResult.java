package com.xyz;

import sootup.core.model.SootMethod;

public class SSLOverwriteResult {

    SootMethod sootMethod;
    boolean containsProceedCall = false;
    boolean containsProceedCallString = false;
    boolean callAlwaysReachable = false;
    boolean onlyParamNullChecked = false;

    public SootMethod getSootMethod() {
        return sootMethod;
    }

    public void setSootMethod(SootMethod sootMethod) {
        this.sootMethod = sootMethod;
    }

    public boolean isContainsProceedCall() {
        return containsProceedCall;
    }

    public void setContainsProceedCall(boolean containsProceedCall) {
        this.containsProceedCall = containsProceedCall;
    }

    public boolean isContainsProceedCallString() {
        return containsProceedCallString;
    }

    public void setContainsProceedCallString(boolean containsProceedCallString) {
        this.containsProceedCallString = containsProceedCallString;
    }

    public boolean isCallAlwaysReachable() {
        return callAlwaysReachable;
    }

    public void setCallAlwaysReachable(boolean callAlwaysReachable) {
        this.callAlwaysReachable = callAlwaysReachable;
    }

    public boolean isOnlyParamNullChecked() {
        return onlyParamNullChecked;
    }

    public void setOnlyParamNullChecked(boolean onlyParamNullChecked) {
        this.onlyParamNullChecked = onlyParamNullChecked;
    }
}
