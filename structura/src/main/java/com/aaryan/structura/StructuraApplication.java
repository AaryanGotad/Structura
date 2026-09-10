package com.aaryan.structura;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestClient;

@SpringBootApplication(scanBasePackages = "com.aaryan")
public class StructuraApplication {

	public static void main(String[] args) {
		SpringApplication.run(StructuraApplication.class, args);
	}

	@Bean
	public RestClient restClient() {
		return RestClient.create();
	}

}
