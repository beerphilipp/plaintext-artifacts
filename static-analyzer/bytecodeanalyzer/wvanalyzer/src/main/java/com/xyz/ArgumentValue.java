package com.xyz;

import java.util.List;

public abstract class ArgumentValue {
    private String source;
    private Object value;

    public ArgumentValue(String source, Object value) {
        this.source = source;
        this.value = value;
    }

    public String getSource() {
        return source;
    }


    public abstract Object getValue();

    @Override
    public String toString() {
        return "ArgumentValue{" +
                "source='" + source + '\'' +
                ", value=" + value +
                '}';
    }

}
