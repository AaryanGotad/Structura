package com.aaryan.structura;

import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import com.aaryan.structura.dto.AltPredDTO;
import com.aaryan.structura.dto.AnalyzeRequestDTO;
import com.aaryan.structura.dto.AnalyzeResponseDTO;
import com.aaryan.structura.dto.SentPredDTO;

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

    // private static final Pattern SENTENCE_PATTERN = Pattern.compile("[^.!?]+[.!?]+");
    // private static final String[] CLASSES = {
    //         "BACKGROUND", "OBJECTIVE", "METHOD", "RESULTS", "CONCLUSION"
    // };

    // private final ObjectWriter prettyJsonWriter;

    private final RestClient restClient;

    public AbstractAnalysisService(RestClient restClient) {
        // this.prettyJsonWriter = objectMapper.writerWithDefaultPrettyPrinter();
        this.restClient = restClient;
    }

    public AnalyzeResponseDTO analyze(String text, String targeturl) {
        AnalyzeRequestDTO payload = new AnalyzeRequestDTO(text);

        return restClient.post()
                .uri(targeturl)
                .contentType(MediaType.APPLICATION_JSON)
                .body(payload)
                .retrieve()
                .body(new ParameterizedTypeReference<AnalyzeResponseDTO>() {});
    }

    //     List<String> sentences = splitSentences(text);
    //     List<SentPredDTO> structure = new ArrayList<>();
    //     int classIndex = 0;
    //     int sentencesPerClass = Math.max(1, (int) Math.ceil(sentences.size() / 5.0));

    //     for (int index = 0; index < sentences.size(); index++) {
    //         // Assign sentences to classes in a round-robin manner
    //         // Shift to the next class after all sentences for the current class have been assigned
    //         if (index > 0 && index % sentencesPerClass == 0 && classIndex < CLASSES.length - 1) {
    //             classIndex++;
    //         }

    //         int nextClassIndex = (classIndex + 1) % CLASSES.length;
    //         // Create a SentPredDTO with the current sentence, predicted class, confidence, and alternative prediction
    //         structure.add(new SentPredDTO(
    //                 sentences.get(index).trim(), // Trim whitespace from the sentence
    //                 CLASSES[classIndex],
    //                 confidence(0.75, 0.24), // Generate a random confidence value between 0.75 and 0.99
    //                 new AltPredDTO(CLASSES[nextClassIndex], confidence(0.05, 0.15)) // Generate a random confidence value for the alternative prediction between 0.05 and 0.20
    //         ));
    //     }

    //     try {
    //         return new AnalyzeResponseDTO(true, structure, prettyJsonWriter.writeValueAsString(structure));
    //     } catch (JacksonException exception) {
    //         throw new IllegalStateException("Unable to serialize analysis output", exception);
    //     }
    // }

    // private List<String> splitSentences(String text) {
    //     var matcher = SENTENCE_PATTERN.matcher(text);
    //     List<String> sentences = new ArrayList<>();
    //     while (matcher.find()) {
    //         sentences.add(matcher.group());
    //     }
    //     return sentences.isEmpty() ? List.of(text) : sentences;
    // }

    // private double confidence(double minimum, double range) {
    //     double value = minimum + ThreadLocalRandom.current().nextDouble() * range;
    //     return BigDecimal.valueOf(value).setScale(3, RoundingMode.HALF_UP).doubleValue();
    // }
}