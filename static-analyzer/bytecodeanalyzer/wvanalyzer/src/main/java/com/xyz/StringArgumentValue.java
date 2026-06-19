package com.xyz;

public class StringArgumentValue extends ArgumentValue {

    String source;
    String value;

    public StringArgumentValue(String source, String value) {
        super(source, value);
        this.source = source;
        this.value = value;
    }

    @Override
    public String getSource() {
        return this.source;
    }

    @Override
    public String getValue() {
        return super.getSource();
    }
}
