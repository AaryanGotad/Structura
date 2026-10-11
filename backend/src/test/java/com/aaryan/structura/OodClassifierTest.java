package com.aaryan.structura;

import com.aaryan.structura.dto.SentPredDTO;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class OodClassifierTest {

    private final OodClassifier classifier = new OodClassifier();

    @Test
    void flagsLowMeanConfidence() {
        assertTrue(classifier.isLikelyOOD(List.of(
                prediction("BACKGROUND", 0.40),
                prediction("BACKGROUND", 0.50),
                prediction("METHODS", 0.40)
        )));
    }

    @Test
    void treatsConfidenceAtThresholdAsInDomainWhenOtherRulesPass() {
        assertFalse(classifier.isLikelyOOD(List.of(
                prediction("BACKGROUND", 0.45),
                prediction("BACKGROUND", 0.45),
                prediction("METHODS", 0.45)
        )));
    }

    @Test
    void flagsHighPredictionVolatility() {
        assertTrue(classifier.isLikelyOOD(List.of(
                prediction("BACKGROUND", 0.80),
                prediction("RESULTS", 0.80),
                prediction("OBJECTIVE", 0.80),
                prediction("CONCLUSIONS", 0.80)
        )));
    }

    @Test
    void acceptsStablePredictionsWithValidSentenceCount() {
        assertFalse(classifier.isLikelyOOD(List.of(
                prediction("BACKGROUND", 0.80),
                prediction("BACKGROUND", 0.80),
                prediction("METHODS", 0.80),
                prediction("METHODS", 0.80),
                prediction("RESULTS", 0.80)
        )));
    }

    @Test
    void flagsSentenceCountsOutsideInclusiveBounds() {
        assertTrue(classifier.isLikelyOOD(List.of(
                prediction("BACKGROUND", 0.80),
                prediction("BACKGROUND", 0.80)
        )));

        List<SentPredDTO> thirtyOnePredictions = new ArrayList<>();
        for (int index = 0; index < 31; index++) {
            thirtyOnePredictions.add(prediction("BACKGROUND", 0.80));
        }

        assertTrue(classifier.isLikelyOOD(thirtyOnePredictions));
    }

    private static SentPredDTO prediction(String predictedClass, double confidence) {
        return new SentPredDTO("sentence", predictedClass, confidence, null, List.of());
    }
}