package com.aaryan.structura.dto;

import java.util.List;

public record MlAnalyzeResponseDTO(
        boolean success,
        List<SentPredDTO> data,
        String rawOutput
) {
}