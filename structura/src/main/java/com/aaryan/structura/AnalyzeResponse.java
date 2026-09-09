package com.aaryan.structura;

import java.util.List;

public record AnalyzeResponse(
        boolean success,
        List<SentencePrediction> data,
        String rawOutput
) {
}