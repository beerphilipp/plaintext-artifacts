package com.xyz;

import sootup.analysis.intraprocedural.ForwardFlowAnalysis;
import sootup.core.graph.BasicBlock;
import sootup.core.graph.StmtGraph;
import sootup.core.jimple.basic.Local;
import sootup.core.jimple.basic.Value;
import sootup.core.jimple.common.constant.NullConstant;
import sootup.core.jimple.common.ref.JParameterRef;
import sootup.core.jimple.common.stmt.*;
import sootup.core.jimple.javabytecode.stmt.JBreakpointStmt;
import sootup.core.jimple.javabytecode.stmt.JEnterMonitorStmt;
import sootup.core.jimple.javabytecode.stmt.JExitMonitorStmt;

import javax.annotation.Nonnull;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public class ParameterNullCheckAnalysis extends ForwardFlowAnalysis<Map<Local, Set<Value>>>  {


    public <B extends BasicBlock<B>> ParameterNullCheckAnalysis(StmtGraph<B> graph) {
        super(graph);
        execute();
    }

    @Nonnull
    @Override
    protected Map<Local, Set<Value>> newInitialFlow() {
        return new HashMap<>();
    }

    @Override
    protected void merge(@Nonnull Map<Local, Set<Value>> in1, @Nonnull Map<Local, Set<Value>> in2, @Nonnull Map<Local, Set<Value>> out) {
        out.clear();
        copy(in1, out);
        for (Map.Entry<Local, Set<Value>> entry : in2.entrySet()) {
            out.computeIfAbsent(entry.getKey(), k -> new HashSet<>()).addAll(entry.getValue());
        }

    }

    @Override
    protected void copy(@Nonnull Map<Local, Set<Value>> source, @Nonnull Map<Local, Set<Value>> dest) {
        dest.clear();
        for (Map.Entry<Local, Set<Value>> entry : source.entrySet()) {
            dest.put(entry.getKey(), new HashSet<>(entry.getValue()));
        }
    }


    @Override
    protected void flowThrough(@Nonnull Map<Local, Set<Value>> in, Stmt d, @Nonnull Map<Local, Set<Value>> out) {
        out.clear();
        out.putAll(in);

        if (d instanceof BranchingStmt) {
            // to stuff here
        } else if (d instanceof FallsThroughStmt) {
            // to stuff
        } else {
            // Return and throw statements
        }

        if (d instanceof JInvokeStmt) {
            // transfers the control flow to another method until the called method returns

            JInvokeStmt invokeStmt = (JInvokeStmt) d;
            try {
                Object invokeExpr = invokeStmt.getInvokeExpr();

            } catch (Throwable t) {
                t.printStackTrace();
            }
            return;

        } else if (d instanceof JAssignStmt) {
            // assigns a value from the right hand-side to the left hand-side.
            // left hand-side of an assignment can be a Local referencing a variable (i.e., a Local) or a FieldRef referencing a Field.
            // right hand-side of an assignment can be an expression (Expr), a Local, a FieldRef, or a Constant.


            JAssignStmt assignStmt = (JAssignStmt) d;
            Value left = assignStmt.getLeftOp();
            Value right = assignStmt.getRightOp();

            if (left instanceof Local) {
                Set<Value> facts = new HashSet<>();

                if (right instanceof JParameterRef) {
                    facts.add(right);
                } else if (right instanceof NullConstant) {
                    facts.add(right);
                } else if (right instanceof Local) {
                    // copy the facts from right-local
                    Set<Value> from = in.get(right);
                    if (from != null) {
                        facts.addAll(from);
                    }
                }
                out.put((Local)  left, facts);
            }

        } else if (d instanceof JIdentityStmt) {
            // similar to a JAssignStmt. Handles assignments of identitiyRefs to make implicit assignments explicit in the StmtGraph.
            // Assign parameters to a Local via JParameterRef like @paramater0: int refering to the first argument of a method
            // Assigns exceptions to a local via JCaughtExceptionRef like @caughtexception: java.lang.Exception
            // Assigns the this variable to a Local via a JThisRef

            JIdentityStmt idStmt = (JIdentityStmt) d;
            Value left = idStmt.getLeftOp();
            Value right = idStmt.getRightOp();
            if (left instanceof Local) {
                Set<Value> facts = new HashSet<>();

                if (right instanceof JParameterRef) {
                    facts.add(right);
                } else if (right instanceof NullConstant) {
                    facts.add(right);
                }
                out.put((Local) left, facts);
            }
            return;

        } else if (d instanceof JEnterMonitorStmt) {
            // marks synchronized blocks of code
        } else if (d instanceof JExitMonitorStmt) {
            // do stuff
        } else if (d instanceof JReturnStmt) {
            // do stuff
        } else if (d instanceof JReturnVoidStmt) {

        }
        else if (d instanceof JBreakpointStmt) {
            // do stuff
        }

    }
}
