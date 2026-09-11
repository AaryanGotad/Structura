// Data Transfer Object for the analyze response

package com.aaryan.structura.dto;

import java.util.List;

public record AnalyzeResponseDTO(
        boolean success,
        List<SentPredDTO> data,
        String rawOutput
) {
}