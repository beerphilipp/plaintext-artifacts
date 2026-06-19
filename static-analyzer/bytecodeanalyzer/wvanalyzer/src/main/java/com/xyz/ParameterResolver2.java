package com.xyz;

import sootup.analysis.intraprocedural.ForwardFlowAnalysis;
import sootup.core.graph.BasicBlock;
import sootup.core.graph.StmtGraph;
import sootup.core.jimple.basic.Local;
import sootup.core.jimple.common.stmt.Stmt;

import javax.annotation.Nonnull;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public class ParameterResolver2 extends ForwardFlowAnalysis<Map<Local, Set<ArgumentValue>>> {

    public <B extends BasicBlock<B>> ParameterResolver2(StmtGraph<B> graph) {
        super(graph);
        execute();
    }


    @Override
    protected void flowThrough(@Nonnull Map<Local, Set<ArgumentValue>> in, Stmt d, @Nonnull Map<Local, Set<ArgumentValue>> out) {


    }

    @Nonnull
    @Override
    protected Map<Local, Set<ArgumentValue>> newInitialFlow() {
        return new HashMap<>();
    }

    @Override
    protected void merge(@Nonnull Map<Local, Set<ArgumentValue>> in1, @Nonnull Map<Local, Set<ArgumentValue>> in2, @Nonnull Map<Local, Set<ArgumentValue>> out) {

    }

    @Override
    protected void copy(@Nonnull Map<Local, Set<ArgumentValue>> source, @Nonnull Map<Local, Set<ArgumentValue>> dest) {

    }


}
