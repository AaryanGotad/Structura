package com.aaryan.structura;

public record SentencePrediction(
        String text,
        String predictedClass,
        double confidence,
        AlternativePrediction alternative
) {
}