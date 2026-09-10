package com.aaryan.structura.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.aaryan.structura.AbstractAnalysisService;
import com.aaryan.structura.dto.AnalyzeRequestDTO;
import com.aaryan.structura.dto.AnalyzeResponseDTO;

@RestController
@RequestMapping("/api")
public class AbstractAnalysisController {

    private final AbstractAnalysisService analysisService;

    public AbstractAnalysisController(AbstractAnalysisService analysisService) {
        this.analysisService = analysisService;
    }

    @PostMapping("/analyze")
    public ResponseEntity<AnalyzeResponseDTO> analyze(@RequestBody AnalyzeRequestDTO request) {
        if (request == null || request.text() == null || request.text().isBlank()) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).build();
        }
        return ResponseEntity.ok(analysisService.analyze(request.text(), "http://localhost:8000/analyze"));
    }
}