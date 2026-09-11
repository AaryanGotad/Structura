// Data Transfer Object for the alternative prediction

package com.aaryan.structura.dto;

public record AltPredDTO(
        String predictedClass,
        double confidence
) {
}