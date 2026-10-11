package com.aaryan.structura;

import com.aaryan.structura.dto.SentPredDTO;

import java.util.List;

public class OodClassifier {

    static final double LOW_MEAN_CONFIDENCE_THRESHOLD = 0.45;
    static final double HIGH_VOLATILITY_THRESHOLD = 0.67;
    static final int MIN_SENTENCE_COUNT = 3;
    static final int MAX_SENTENCE_COUNT = 30;

    public boolean isLikelyOOD(List<SentPredDTO> predictions) {
        if (predictions == null) {
            return true;
        }

        return hasInvalidSentenceCount(predictions)
                || hasLowMeanConfidence(predictions)
                || hasHighPredictionVolatility(predictions);
    }

    private boolean hasInvalidSentenceCount(List<SentPredDTO> predictions) {
        int sentenceCount = predictions.size();
        return sentenceCount < MIN_SENTENCE_COUNT || sentenceCount > MAX_SENTENCE_COUNT;
    }

    private boolean hasLowMeanConfidence(List<SentPredDTO> predictions) {
        if (predictions.isEmpty()) {
            return true;
        }

        double totalConfidence = predictions.stream()
                .mapToDouble(SentPredDTO::confidence)
                .sum();
        double meanConfidence = totalConfidence / predictions.size();
        return meanConfidence < LOW_MEAN_CONFIDENCE_THRESHOLD;
    }

    private boolean hasHighPredictionVolatility(List<SentPredDTO> predictions) {
        if (predictions.size() < 2) {
            return false;
        }

        int classChanges = 0;
        for (int index = 1; index < predictions.size(); index++) {
            String previousClass = predictions.get(index - 1).predictedClass();
            String currentClass = predictions.get(index).predictedClass();
            if (!java.util.Objects.equals(previousClass, currentClass)) {
                classChanges++;
            }
        }

        double changeRate = (double) classChanges / (predictions.size() - 1);
        return changeRate >= HIGH_VOLATILITY_THRESHOLD;
    }
}