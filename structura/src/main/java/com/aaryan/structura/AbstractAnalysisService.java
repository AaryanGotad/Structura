package com.aaryan.structura;

import org.springframework.stereotype.Service;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;
import tools.jackson.databind.ObjectWriter;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;
import java.util.regex.Pattern;

@Service
public class AbstractAnalysisService {

    private static final Pattern SENTENCE_PATTERN = Pattern.compile("[^.!?]+[.!?]+");
    private static final String[] CLASSES = {
            "BACKGROUND", "OBJECTIVE", "METHOD", "RESULTS", "CONCLUSION"
    };

    private final ObjectWriter prettyJsonWriter;

    public AbstractAnalysisService(ObjectMapper objectMapper) {
        this.prettyJsonWriter = objectMapper.writerWithDefaultPrettyPrinter();
    }

    public AnalyzeResponse analyze(String text) {
        List<String> sentences = splitSentences(text);
        List<SentencePrediction> structure = new ArrayList<>();
        int classIndex = 0;
        int sentencesPerClass = Math.max(1, (int) Math.ceil(sentences.size() / 5.0));

        for (int index = 0; index < sentences.size(); index++) {
            if (index > 0 && index % sentencesPerClass == 0 && classIndex < CLASSES.length - 1) {
                classIndex++;
            }

            int nextClassIndex = (classIndex + 1) % CLASSES.length;
            structure.add(new SentencePrediction(
                    sentences.get(index).trim(),
                    CLASSES[classIndex],
                    confidence(0.75, 0.24),
                    new AlternativePrediction(CLASSES[nextClassIndex], confidence(0.05, 0.15))
            ));
        }

        try {
            return new AnalyzeResponse(true, structure, prettyJsonWriter.writeValueAsString(structure));
        } catch (JacksonException exception) {
            throw new IllegalStateException("Unable to serialize analysis output", exception);
        }
    }

    private List<String> splitSentences(String text) {
        var matcher = SENTENCE_PATTERN.matcher(text);
        List<String> sentences = new ArrayList<>();
        while (matcher.find()) {
            sentences.add(matcher.group());
        }
        return sentences.isEmpty() ? List.of(text) : sentences;
    }

    private double confidence(double minimum, double range) {
        double value = minimum + ThreadLocalRandom.current().nextDouble() * range;
        return BigDecimal.valueOf(value).setScale(3, RoundingMode.HALF_UP).doubleValue();
    }
}