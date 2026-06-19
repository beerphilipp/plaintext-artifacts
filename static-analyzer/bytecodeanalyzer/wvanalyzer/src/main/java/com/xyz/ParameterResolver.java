package com.xyz;

import sootup.core.graph.StmtGraph;
import sootup.core.jimple.basic.Immediate;
import sootup.core.jimple.basic.Local;
import sootup.core.jimple.basic.Value;
import sootup.core.jimple.common.constant.Constant;
import sootup.core.jimple.common.constant.IntConstant;
import sootup.core.jimple.common.constant.StringConstant;
import sootup.core.jimple.common.expr.AbstractInvokeExpr;
import sootup.core.jimple.common.expr.JVirtualInvokeExpr;
import sootup.core.jimple.common.ref.JParameterRef;
import sootup.core.jimple.common.stmt.AbstractDefinitionStmt;
import sootup.core.jimple.common.stmt.Stmt;
import sootup.core.model.Body;
import sootup.core.model.SootMethod;
import sootup.java.core.views.JavaView;

import java.util.*;

public class ParameterResolver {

    private final JavaView javaView;

    public ParameterResolver(JavaView javaView) {
        this.javaView = javaView;
    }

    public Set<ArgumentValue> getParameterValue(CallLocation callLocation, int paramIndex) {
        Stmt stmt = callLocation.getStmt();

        AbstractInvokeExpr invokeExpr = stmt.asInvokableStmt()
                .getInvokeExpr()
                .orElseThrow(() -> new RuntimeException(
                        "Invoke expression is null for statement: " + stmt));

        if (invokeExpr.getArgCount() <= paramIndex) {
            throw new RuntimeException("Parameter index " + paramIndex + " is out of bounds for method " + invokeExpr.getMethodSignature() + " with " + invokeExpr.getArgCount() + " parameters.");
        }

        Immediate arg = invokeExpr.getArg(paramIndex);

        SootMethod method = callLocation.getMethod();
        Body body = method.getBody();

        return resolveValues(arg, stmt, body.getStmtGraph(), new HashSet<>());


    }

    private Set<ArgumentValue> resolveValues(Immediate value, Stmt use, StmtGraph<?> stmtGraph, Set<Local> seen) {
        Set<ArgumentValue> results = new HashSet<>();

        if (value instanceof Constant) {
            if (value instanceof StringConstant) {
                results.add(new StringArgumentValue("StringConstant", ((StringConstant) value).getValue()));
            } else if (value instanceof IntConstant) {
                results.add(new IntArgumentValue("IntConstant", ((IntConstant) value).getValue()));
            } else {
                System.err.println("Constant is not a string or int: " + value);
            }
            return results;
        } else if (value instanceof Local) {
            Local local = (Local) value;
            if (!seen.add(local)) {
                // if we have already seen this local, we are in a cycle, so we stop here
                return results;
            }

            for (AbstractDefinitionStmt def : getReachingDefinitions(local, use, stmtGraph)) {
                Value rhs = def.getRightOp();
                if (rhs instanceof Immediate) {
                    results.addAll(resolveValues((Immediate) rhs, def, stmtGraph, seen));
                } else if (rhs instanceof JParameterRef) {
                    results.add(new UnknownArgumentValue("JParamRef"));
                    System.out.println("Right-hand side is a parameter reference: " + rhs);
                } else if (rhs instanceof JVirtualInvokeExpr) {
                    results.add(new UnknownArgumentValue("JVirtualInvokeExpr"));
                }
                else {
                    results.add(new UnknownArgumentValue("UNKNOWN_1_" + rhs.getClass()));
                    System.err.println("Right-hand side is not an immediate nor parameter reference: " + rhs);
                    System.out.println(rhs.getClass());
                }
            }
        } else {
            System.err.println("Value is neither a constant nor a local: " + value);
            results.add(new UnknownArgumentValue("UNKNOWN_2"));
        }
        return results;
    }

    private Set<AbstractDefinitionStmt> getReachingDefinitions(Local local, Stmt use, StmtGraph<?> stmtGraph) {
        Set<AbstractDefinitionStmt> results = new HashSet<>();
        Set<Stmt> visited = new HashSet<>();
        Deque<Stmt> worklist = new ArrayDeque<>(stmtGraph.predecessors(use));

        while (!worklist.isEmpty()) {
            Stmt current = worklist.pop();
            if (!visited.add(current)) {
                continue;
            }

            if (current instanceof AbstractDefinitionStmt) {
                AbstractDefinitionStmt def = (AbstractDefinitionStmt) current;
                if (def.getLeftOp() instanceof Local && def.getLeftOp().equals(local)) {
                    results.add(def);
                    // kill earlier defs here
                    continue;
                }
            }
            worklist.addAll(stmtGraph.predecessors(current));
        }
        return results;
    }
}
