// Data Transfer Object for the analyze response

package com.aaryan.structura.dto;

public record SentPredDTO(
        String text,
        String predictedClass,
        double confidence,
        AltPredDTO alternative
) {
}