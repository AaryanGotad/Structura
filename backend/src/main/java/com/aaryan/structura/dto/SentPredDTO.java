// Data Transfer Object for the analyze response

package com.aaryan.structura.dto;

import java.util.List;

public record SentPredDTO(
        String text,
        String predictedClass,
        double confidence,
        AltPredDTO alternative,
        List<Double> rawScores
) {
}