// ========== UI HELPERS ==========
const UI = {
    // Show Full Screen Loader
    showLoader(message = 'Analyse par IA en cours...') {
        // Remove existing loader if any
        const existing = document.querySelector('.loader-overlay');
        if (existing) existing.remove();

        const overlay = document.createElement('div');
        overlay.className = 'loader-overlay';
        overlay.innerHTML = `
            <div class="spinner"></div>
            <div style="margin-top: 20px; font-weight: 600; color: var(--neutral-700);">${message}</div>
        `;
        document.body.appendChild(overlay);
        return overlay;
    },

    hideLoader() {
        const overlay = document.querySelector('.loader-overlay');
        if (overlay) {
            overlay.style.opacity = '0';
            setTimeout(() => overlay.remove(), 300);
        }
    },

    showAlert(message, type = 'info') {
        const container = document.querySelector('.form-section');
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;

        // Insert at top of form
        const card = container.querySelector('.card');
        card.insertBefore(alertDiv, card.firstChild);

        setTimeout(() => alertDiv.remove(), 5000);
    },

    // Toggle between Intro and Result cards
    showResultCard() {
        const introCard = document.getElementById('introCard');
        const resultCard = document.getElementById('resultCard');

        if (introCard) introCard.classList.add('hidden');
        if (resultCard) {
            resultCard.style.display = 'block'; // Ensure it's not display:none
            // Small delay to allow display:block to apply before transition
            setTimeout(() => {
                resultCard.classList.add('visible');
            }, 10);
        }
    },

    resetResultView() {
        const introCard = document.getElementById('introCard');
        const resultCard = document.getElementById('resultCard');

        if (introCard) introCard.classList.remove('hidden');
        if (resultCard) resultCard.classList.remove('visible');
    },

    animateProbability(probability) {
        // probability is 0.0 to 1.0
        const percentage = Math.round(probability * 100);
        const circle = document.getElementById('probCircle');
        const text = document.getElementById('probText');

        if (!circle || !text) return;

        // Reset
        circle.style.strokeDasharray = "0, 100";

        // Color logic
        let color = '#10b981'; // Green (Safe)
        if (percentage > 50) color = '#ef4444'; // Red (Danger)
        else if (percentage > 20) color = '#f59e0b'; // Orange (Warning)

        circle.style.stroke = color;

        // Animate
        setTimeout(() => {
            circle.style.strokeDasharray = `${percentage}, 100`;
            text.textContent = `${percentage}%`;
            text.style.fill = color;
        }, 100);
    },

    updateInputError(input, message) {
        const group = input.closest('.form-group');
        const errorMsg = group.querySelector('.error-msg');

        if (message) {
            input.classList.add('error');
            if (errorMsg) errorMsg.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> ${message}`;
        } else {
            input.classList.remove('error');
        }
    },

    switchTab(tabName) {
        // Buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
            btn.style.borderBottom = 'none';
            btn.style.fontWeight = '500';
            btn.style.color = 'var(--neutral-500)';

            if (btn.dataset.tab === tabName) {
                btn.classList.add('active');
                btn.style.borderBottom = '2px solid var(--primary-color)';
                btn.style.fontWeight = '600';
                btn.style.color = 'var(--primary-color)';
            }
        });

        // Content
        const shapCont = document.getElementById('shap-container');
        const limeCont = document.getElementById('lime-container');

        if (tabName === 'shap') {
            if (shapCont) shapCont.style.display = 'block';
            if (limeCont) limeCont.style.display = 'none';
        } else {
            if (shapCont) shapCont.style.display = 'none';
            if (limeCont) limeCont.style.display = 'block';

            // Fix Plotly resize issue when unhiding
            try {
                const limePlot = document.getElementById('lime-mini-chart');
                if (limePlot) Plotly.Plots.resize(limePlot);
            } catch (e) { }
        }
    }
};

// ========== FORM LOGIC ==========
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("cancerForm");

    if (!form) return;

    // Real-time Validation (Binds to all inputs)
    form.querySelectorAll('input, select').forEach(input => {
        input.addEventListener('input', () => {
            UI.updateInputError(input, null); // Clear error on type
        });

        if (input.id === 'BMI') {
            input.addEventListener('blur', validateBMI);
        }
    });

    // Age Change Logic (Conditional Fields)
    const ageSelect = document.getElementById("AgeCategory");
    if (ageSelect) {
        ageSelect.addEventListener("change", handleAgeChange);
        handleAgeChange(); // Init
    }

    // Submit
    form.addEventListener("submit", handleFormSubmit);
});

function validateBMI() {
    const input = document.getElementById("BMI");
    const val = parseFloat(input.value);

    if (isNaN(val) || val < 10 || val > 60) {
        UI.updateInputError(input, "IMC invalide (10-60)");
        return false;
    }
    return true;
}

function handleAgeChange() {
    const ageSelect = document.getElementById("AgeCategory");
    const diabeticGroup = document.getElementById("diabeticGroup");

    // Logic: If Age < 30, Diabetes risk is often lower or different, 
    // but the original logic was hiding it. Let's keep it visible but maybe highlight relevant fields?
    // Actually, following original logic: if young, maybe hide to simplify?
    // Original Code: if (age >= 50) show diabetic.

    // Parsing text like "18-24" -> 18
    const val = ageSelect.value;
    const minAge = parseInt(val.split('-')[0]) || 80; // "80 or older" -> 80

    if (diabeticGroup) {
        if (minAge < 30) {
            // Let's keep it clean: if very young, maybe auto-set No or hide?
            // Original logic was hide if < 50. That seems too aggressive for "professional" app (young people have type 1).
            // Let's ALWAYS show it for professional completeness, but maybe pre-select No if just changing?
            // No, let's stick to user intent. I will show it always for better UX (hiding fields is confusing).
            // But I will keep the listener in case we want to add "Recommended" badges later.
            diabeticGroup.style.display = 'block';
        } else {
            diabeticGroup.style.display = 'block';
        }
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();

    if (!validateBMI()) return;

    const form = e.target;
    const formData = new FormData(form);

    UI.showLoader();

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            displayResults(data);
        } else {
            throw new Error("Erreur serveur");
        }
    } catch (err) {
        UI.showAlert("Erreur lors de la prédiction: " + err.message, "danger");
    } finally {
        UI.hideLoader();
    }
}

function displayResults(data) {
    UI.showResultCard();

    const statusBadges = document.getElementById('resultStatus');
    const actions = document.getElementById('resultActions');

    // Status Badge
    const isRisky = (data.prediction === 1 || data.prediction === 'Yes');

    if (isRisky) {
        statusBadges.className = 'prediction-badge danger';
        statusBadges.textContent = '⚠️ Risque Identifié';
    } else {
        statusBadges.className = 'prediction-badge safe';
        statusBadges.textContent = '✅ Aucun Risque Détecté';
    }

    // Probability
    const prob = data.probability; // 0.0 to 1.0 expected
    UI.animateProbability(prob);

    // SHAP / Explanation
    // SHAP / Explanation
    renderExplanation(data.explanation, 'shap');

    // LIME
    if (data.lime_explanation) {
        console.log("LIME Data:", data.lime_explanation);
        renderLimeExplanation(data.lime_explanation);
    }

    // Show Report Button
    if (actions) actions.classList.remove('hidden');
    setupReportButton();
}

function renderExplanation(expl, type = 'shap') {
    const containerId = type === 'shap' ? 'shap-container' : 'lime-container';
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!expl || expl.error) {
        container.innerHTML = `<p class="text-center text-muted">Explication non disponible</p>`;
        return;
    }

    // Clear
    container.innerHTML = '';

    // Title
    const header = document.createElement('h4');
    header.style.fontSize = '0.95rem';
    header.style.marginBottom = '10px';
    header.innerHTML = '<i class="fa-solid fa-list-check"></i> Facteurs Influents (Global)';
    container.appendChild(header);

    // Legend
    const legend = document.createElement('div');
    legend.innerHTML = `
        <div style="display:flex; gap:15px; font-size:0.8rem; margin-bottom:10px; color:var(--neutral-600);">
            <div style="display:flex; align-items:center; gap:5px;">
                <span style="width:10px; height:10px; background:#ef4444; display:inline-block; border-radius:50%;"></span>
                Augmente le risque
            </div>
            <div style="display:flex; align-items:center; gap:5px;">
                <span style="width:10px; height:10px; background:#10b981; display:inline-block; border-radius:50%;"></span>
                Diminue le risque
            </div>
        </div>
    `;
    container.appendChild(legend);

    // Top Features List (Standardized)
    if (expl.top_features && Array.isArray(expl.top_features)) {
        const ul = document.createElement('ul');
        ul.style.fontSize = '0.9rem';

        expl.top_features.slice(0, 5).forEach(f => {
            const li = document.createElement('li');
            li.style.marginBottom = '6px';
            li.style.display = 'flex';
            li.style.justifyContent = 'space-between';

            const isRiskFactor = f.shap_value > 0;
            const color = isRiskFactor ? 'var(--danger-color)' : 'var(--success-color)';
            const icon = isRiskFactor ? 'fa-arrow-up' : 'fa-arrow-down';

            li.innerHTML = `
                <span>${f.feature}</span>
                <span style="color: ${color}; font-weight: 600;">
                    <i class="fa-solid ${icon}"></i> ${Math.abs(f.shap_value).toFixed(2)}
                </span>
            `;
            ul.appendChild(li);
        });
        container.appendChild(ul);
    }

    // Full Chart (Plotly)
    if (expl.all_features && window.Plotly) {
        const chartDiv = document.createElement('div');
        chartDiv.id = 'shap-mini-chart';
        chartDiv.style.marginTop = '15px';
        chartDiv.style.height = '250px';
        container.appendChild(chartDiv);

        const names = expl.all_features.map(x => x.feature).slice(0, 10); // Check reverse if needed
        const values = expl.all_features.map(x => x.shap_value).slice(0, 10);

        const colors = values.map(v => v > 0 ? '#ef4444' : '#10b981');

        Plotly.newPlot(chartDiv, [{
            x: values,
            y: names,
            type: 'bar',
            orientation: 'h',
            marker: { color: colors }
        }], {
            margin: { l: 100, r: 20, t: 0, b: 30 },
            barmode: 'relative',
            height: 250,
            xaxis: { fixedrange: true },
            yaxis: { fixedrange: true, automargin: true }
        }, { displayModeBar: false });
    }
}

function setupReportButton() {
    const btn = document.getElementById('generate-report-btn');
    // Remove old listeners by cloning
    // Helper to safely re-bind
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);

    newBtn.addEventListener('click', async () => {
        newBtn.disabled = true;
        newBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Génération...';

        const form = document.getElementById('cancerForm');
        const formData = new FormData(form);

        try {
            const resp = await fetch('/report', { method: 'POST', body: formData });
            if (resp.ok) {
                const blob = await resp.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'Rapport_Analyse_Sante.pdf';
                document.body.appendChild(a);
                a.click();
                a.remove();
            } else {
                UI.showAlert("Erreur génération PDF", "danger");
            }
        } catch (e) {
            UI.showAlert("Erreur réseau", "danger");
        } finally {
            newBtn.disabled = false;
            newBtn.innerHTML = '<i class="fa-solid fa-file-pdf"></i> Télécharger le Rapport';
        }
    });
}

function renderLimeExplanation(limeData) {
    const container = document.getElementById('lime-container');
    if (!container) return;

    container.innerHTML = '';

    if (limeData.error) {
        container.innerHTML = `<p class="text-center text-muted">Erreur LIME: ${limeData.error}</p>`;
        return;
    }

    if (!limeData.explanation || !Array.isArray(limeData.explanation)) {
        container.innerHTML = `<p class="text-center text-muted">Pas de données LIME</p>`;
        return;
    }

    const explanation = limeData.explanation;

    // Title
    const header = document.createElement('h4');
    header.style.fontSize = '0.95rem';
    header.style.marginBottom = '10px';
    header.innerHTML = '<i class="fa-solid fa-microscope"></i> Facteurs Locaux (LIME)';
    container.appendChild(header);

    // Legend
    const legend = document.createElement('div');
    legend.innerHTML = `
        <div style="display:flex; gap:15px; font-size:0.8rem; margin-bottom:10px; color:var(--neutral-600);">
            <div style="display:flex; align-items:center; gap:5px;">
                <span style="width:10px; height:10px; background:#ef4444; display:inline-block; border-radius:50%;"></span>
                Augmente le risque
            </div>
            <div style="display:flex; align-items:center; gap:5px;">
                <span style="width:10px; height:10px; background:#3b82f6; display:inline-block; border-radius:50%;"></span>
                Diminue le risque
            </div>
        </div>
    `;
    container.appendChild(legend);

    // LIME Values List
    const ul = document.createElement('ul');
    ul.style.fontSize = '0.9rem';

    // limeData.explanation is sorted by absolute value
    explanation.slice(0, 5).forEach(f => {
        const li = document.createElement('li');
        li.style.marginBottom = '6px';
        li.style.display = 'flex';
        li.style.justifyContent = 'space-between';

        const isRiskFactor = f.value > 0;
        const color = isRiskFactor ? '#ef4444' : '#3b82f6';
        const icon = isRiskFactor ? 'fa-arrow-up' : 'fa-arrow-down';

        li.innerHTML = `
            <span>${f.feature}</span>
            <span style="color: ${color}; font-weight: 600;">
                <i class="fa-solid ${icon}"></i> ${Math.abs(f.value).toFixed(4)}
            </span>
        `;
        ul.appendChild(li);
    });
    container.appendChild(ul);

    // Plotly Chart
    const chartDiv = document.createElement('div');
    chartDiv.id = 'lime-mini-chart';
    chartDiv.style.marginTop = '15px';
    chartDiv.style.height = '250px';
    container.appendChild(chartDiv);

    // Sort: most important at top (Plotly needs reverse order for h-bar)
    // limeData.explanation is sorted descending by absolute value
    // Let's take top 10
    const top10 = explanation.slice(0, 10).reverse();

    const names = top10.map(x => x.feature);
    const values = top10.map(x => x.value);
    const colors = values.map(v => v > 0 ? '#ef4444' : '#3b82f6'); // Red vs Blue for LIME convention

    Plotly.newPlot(chartDiv, [{
        x: values,
        y: names,
        type: 'bar',
        orientation: 'h',
        marker: { color: colors }
    }], {
        margin: { l: 150, r: 20, t: 0, b: 30 },
        barmode: 'relative',
        height: 250,
        xaxis: { fixedrange: true },
        yaxis: { fixedrange: true, automargin: true }
    }, { displayModeBar: false });
}
