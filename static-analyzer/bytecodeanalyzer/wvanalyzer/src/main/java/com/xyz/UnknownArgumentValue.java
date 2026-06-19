package com.xyz;

public class UnknownArgumentValue extends ArgumentValue {
    String source;

    public UnknownArgumentValue(String source) {
        super(source, null);
        this.source = source;
    }

    @Override
    public String getSource() {
        return this.source;
    }

    @Override
    public Object getValue() {
        return null;
    }
}
