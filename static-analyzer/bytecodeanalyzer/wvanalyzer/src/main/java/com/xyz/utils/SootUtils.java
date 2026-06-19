package com.xyz.utils;

import sootup.core.model.SootClass;
import sootup.core.types.ClassType;
import sootup.java.core.views.JavaView;

public class SootUtils {

    /**
     * Check if clazz is a subclass of superClazz.
     * @param view The JavaView to use for class lookups
     * @param clazz The class to check
     * @param superClazz The potential superclass
     * @return true if clazz is a subclass of superClazz, false otherwise
     */
    public static boolean isClassSubclass(JavaView view, SootClass clazz, SootClass superClazz) {
        if (clazz == null || superClazz == null) {
            return false;
        }
        if (clazz.equals(superClazz)) {
            return true;
        }

        boolean hasSuperClazz;

        try {
            hasSuperClazz = clazz.getSuperclass().isPresent();
        } catch (Exception e) {
            return false;
        }

        if (hasSuperClazz) {
            if (clazz.getSuperclass().isEmpty()) {
                return false;
            }
            ClassType clazzType = clazz.getSuperclass().get();
            SootClass newClass = view.getClass(clazzType).orElse(null);
            return isClassSubclass(view, newClass, superClazz);
        }
        return false;
    }
}
