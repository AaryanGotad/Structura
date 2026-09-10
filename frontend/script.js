const ThemeManager = {
    init() {
        const savedTheme = localStorage.getItem('structura-theme');
        const themeToApply = savedTheme === 'light' ? 'light' : 'dark';
        this.setTheme(themeToApply);
        
        document.getElementById('themeToggle').addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            this.setTheme(newTheme);
        });
    },
    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('structura-theme', theme);
    }
};

const SAMPLE_ABSTRACTS = [
    {
        topic: "Oncology",
        text: "Immune checkpoint inhibitors (ICIs) have revolutionized the treatment of advanced non-small cell lung cancer (NSCLC). However, identifying patients who will derive long-term benefit remains challenging. We aimed to evaluate the predictive value of baseline systemic inflammatory markers in patients treated with ICIs. We retrospectively analyzed 245 patients with advanced NSCLC treated with anti-PD-1 therapy at our institution between 2018 and 2022. The derived neutrophil-to-lymphocyte ratio (dNLR) was calculated from baseline blood counts. Patients with a high baseline dNLR had a significantly shorter median progression-free survival (3.2 vs. 6.8 months; p<0.001) and overall survival (8.5 vs. 18.2 months; p<0.001) compared to those with a low dNLR. Elevated baseline dNLR is an independent prognostic factor for poor clinical outcomes in NSCLC patients undergoing ICI therapy. These readily available biomarkers may help guide treatment decisions."
    },
    {
        topic: "Cardiology",
        text: "Heart failure with preserved ejection fraction (HFpEF) represents a major and growing public health issue with limited therapeutic options. This study sought to determine the efficacy of Sodium-Glucose Cotransporter 2 (SGLT2) inhibitors in reducing cardiovascular events in patients with HFpEF. A systematic review and meta-analysis of randomized placebo-controlled trials was conducted. We searched PubMed, Embase, and the Cochrane Library for trials published up to October 2023. Data from 4 major trials comprising 15,234 patients were pooled. Treatment with SGLT2 inhibitors was associated with a 22% relative risk reduction in the primary composite outcome of cardiovascular death or hospitalization for heart failure (Hazard Ratio 0.78, 95% CI 0.73-0.84). The benefit was consistent across various prespecified subgroups. SGLT2 inhibitors significantly reduce the risk of major heart failure events in patients with HFpEF and should be considered a foundational therapy for this condition."
    },
    {
        topic: "Neurology",
        text: "Sleep disturbances are prevalent in Alzheimer's disease (AD) and may contribute to cognitive decline. The objective of this trial was to determine whether a tailored bright light therapy intervention improves sleep quality and cognitive function in mild-to-moderate AD. Fifty community-dwelling patients with AD and confirmed sleep disturbances were randomly assigned to receive either active bright light therapy (10,000 lux) or dim red light (control) for 2 hours daily over 8 weeks. Sleep was assessed via actigraphy, and cognition via the MMSE. Actigraphy revealed a significant increase in total sleep time and sleep efficiency in the active treatment group compared to controls. However, no significant differences were observed in MMSE scores between the two groups at week 8. While bright light therapy effectively improves objective sleep parameters in AD patients, short-term treatment does not appear to provide cognitive benefits."
    }
];

const ApiService = {
    getApiBaseUrl() {
        const { hostname, protocol } = window.location;

        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:8080';
        }

        const forwardedBackendHost = hostname.replace(/-\d+(?=\.app\.github\.dev$)/, '-8080');
        return `${protocol}//${forwardedBackendHost}`;
    },

    async analyzeAbstract(text) {
        const response = await fetch(`${this.getApiBaseUrl()}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });

        if (!response.ok) {
            throw new Error(`Analysis request failed with status ${response.status}`);
        }

        return response.json();
    }
};

const App = {
    elements: {
        input: document.getElementById('abstract-input'),
        btnAnalyze: document.getElementById('btn-analyze'),
        btnClear: document.getElementById('btn-clear'),
        loadingState: document.getElementById('loading-state'),
        resultsContainer: document.getElementById('results-container'),
        samplesGrid: document.getElementById('samples-grid')
    },

    init() {
        ThemeManager.init();
        this.renderSamples();
        this.bindEvents();
    },

    bindEvents() {
        this.elements.btnAnalyze.addEventListener('click', () => this.handleAnalyze());
        this.elements.btnClear.addEventListener('click', () => this.handleClear());
        
        this.elements.input.addEventListener('input', () => {
            this.elements.btnAnalyze.disabled = this.elements.input.value.trim().length === 0;
        });
        this.elements.btnAnalyze.disabled = true;

        document.addEventListener('click', (e) => {
            if (e.target.closest('.raw-toggle-btn')) {
                const popover = document.querySelector('.raw-popover');
                popover.classList.toggle('active');
            } else if (!e.target.closest('.raw-output-wrapper')) {
                const popover = document.querySelector('.raw-popover.active');
                if (popover) popover.classList.remove('active');
            }
            
            const altToggle = e.target.closest('.alt-toggle');
            if (altToggle) {
                const expanded = altToggle.getAttribute('aria-expanded') === 'true';
                altToggle.setAttribute('aria-expanded', !expanded);
            }
        });
    },

    renderSamples() {
        this.elements.samplesGrid.innerHTML = SAMPLE_ABSTRACTS.map((sample, index) => `
            <div class="sample-card">
                <div class="sample-topic">${sample.topic}</div>
                <div class="sample-preview">${sample.text}</div>
                <button class="sample-btn" data-index="${index}">Try this</button>
            </div>
        `).join('');

        document.querySelectorAll('.sample-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = e.target.getAttribute('data-index');
                this.elements.input.value = SAMPLE_ABSTRACTS[index].text;
                this.elements.btnAnalyze.disabled = false;
                
                window.scrollTo({ top: 0, behavior: 'smooth' });
                this.elements.input.focus();
            });
        });
    },

    handleClear() {
        this.elements.input.value = '';
        this.elements.btnAnalyze.disabled = true;
        this.elements.resultsContainer.innerHTML = '';
        this.elements.input.focus();
    },

    async handleAnalyze() {
        const text = this.elements.input.value.trim();
        if (!text) return;

        this.elements.btnAnalyze.disabled = true;
        this.elements.input.disabled = true;
        this.elements.resultsContainer.innerHTML = '';
        this.elements.loadingState.classList.remove('hidden');

        try {
            const result = await ApiService.analyzeAbstract(text);
            this.renderResults(result.data, result.rawOutput);
        } catch (error) {
            console.error("Analysis failed:", error);
            alert("An error occurred during analysis. Please try again.");
        } finally {
            this.elements.loadingState.classList.add('hidden');
            this.elements.btnAnalyze.disabled = false;
            this.elements.input.disabled = false;
        }
    },

    // Generates grouped paragraph HTML where each unique category forms a block
    generateStructuredParagraphsHTML(predictions, useAlternative = false) {
        const groups = [];
        let currentGroup = null;

        predictions.forEach(item => {
            const pClass = useAlternative ? item.alternative.predictedClass : item.predictedClass;
            const pConf = useAlternative ? item.alternative.confidence : item.confidence;

            if (!currentGroup || currentGroup.category !== pClass) {
                if (currentGroup) groups.push(currentGroup);
                currentGroup = {
                    category: pClass,
                    lines: [],
                    totalConfidence: 0
                };
            }
            currentGroup.lines.push(item.text);
            currentGroup.totalConfidence += pConf;
        });
        if (currentGroup) groups.push(currentGroup);

        let html = ``;
        groups.forEach(group => {
            const meanConf = (group.totalConfidence / group.lines.length * 100).toFixed(2);
            const proseText = group.lines.join(' ');
            
            html += `
                <div class="structured-prose-block">
                    <div class="category-header">
                        <span class="category-label">${group.category}</span>
                        <div class="confidence-tooltip">Mean confidence: ${meanConf}%</div>
                    </div>
                    <span class="group-text">${proseText}</span>
                </div>
            `;
        });
        return html;
    },

    renderResults(predictions, rawOutputStr) {
        const primaryHTML = this.generateStructuredParagraphsHTML(predictions, false);
        const altHTML = this.generateStructuredParagraphsHTML(predictions, true);

        const html = `
            <section class="results-section">
                <h2 class="section-heading">Structured abstract</h2>
                <div class="result-card glass-panel">
                    <div class="raw-output-wrapper">
                        <button class="raw-toggle-btn">Raw output</button>
                        <div class="raw-popover">
                            <pre><code>${this.escapeHTML(rawOutputStr)}</code></pre>
                        </div>
                    </div>
                    
                    ${primaryHTML}
                </div> 

                <div class="alt-predictions glass-panel">
                    <button class="alt-toggle" aria-expanded="false">
                        See alternative predictions
                        <svg class="chevron" viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg>
                    </button>
                    <div class="alt-content-wrapper">
                        <div class="alt-content">
                            <div class="alt-content-inner">
                                ${altHTML}
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        `;

        this.elements.resultsContainer.innerHTML = html;
    },

    escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                "'": '&#39;',
                '"': '&quot;'
            }[tag])
        );
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});