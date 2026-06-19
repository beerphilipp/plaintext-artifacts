package com.xyz;

public class IntArgumentValue extends ArgumentValue {

    String source;
    Integer value;

    public IntArgumentValue(String source, Integer value) {
        super(source, value);
        this.source = source;
        this.value = value;
    }

    @Override
    public String getSource() {
        return this.source;
    }

    @Override
    public Integer getValue() {
        return this.value;
    }

}
