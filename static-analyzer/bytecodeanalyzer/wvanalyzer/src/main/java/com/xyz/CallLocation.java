package com.xyz;

import sootup.core.jimple.common.stmt.Stmt;
import sootup.core.model.SootMethod;

public class CallLocation {
    SootMethod method;
    Stmt stmt;

    public CallLocation(SootMethod method, Stmt stmt) {
        this.method = method;
        this.stmt = stmt;
    }

    public SootMethod getMethod() {
        return method;
    }

    public void setMethod(SootMethod method) {
        this.method = method;
    }

    public Stmt getStmt() {
        return stmt;
    }

    public void setStmt(Stmt stmt) {
        this.stmt = stmt;
    }

    @Override
    public String toString() {
        return "CallLocation{" +
                "method=" + method +
                ", stmt=" + stmt +
                '}';
    }
}
