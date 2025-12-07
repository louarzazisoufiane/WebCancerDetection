// ========== UTILITAIRES GLOBALES ==========
const UI = {
    // Afficher une alerte
    showAlert(message, type = 'info', duration = 5000) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        const closeBtn = document.createElement('span');
        closeBtn.className = 'alert-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.onclick = function() { this.parentElement.remove(); };
        
        alertDiv.textContent = message;
        alertDiv.appendChild(closeBtn);
        
        const container = document.querySelector('.container') || document.body;
        container.insertBefore(alertDiv, container.firstChild);
        
        if (duration) {
            setTimeout(() => alertDiv.remove(), duration);
        }
        return alertDiv;
    },

    // Afficher un loader
    showLoader(message = 'Traitement en cours...') {
        const loader = document.createElement('div');
        loader.className = 'loading-text';
        loader.id = 'loader';
        loader.innerHTML = `
            <span class="spinner"></span>
            <span>${message}</span>
        `;
        return loader;
    },

    // Afficher une barre de progression
    updateProgressBar(percentage) {
        let progressBar = document.querySelector('.progress-fill');
        if (!progressBar) {
            const barContainer = document.createElement('div');
            barContainer.className = 'progress-bar';
            barContainer.innerHTML = '<div class="progress-fill"></div>';
            document.body.appendChild(barContainer);
            progressBar = document.querySelector('.progress-fill');
        }
        progressBar.style.width = percentage + '%';
    },

    // Masquer le loader
    hideLoader() {
        const loader = document.getElementById('loader');
        if (loader) loader.remove();
    },

    // Valider un champ
    validateField(field, rules) {
        const value = field.value.trim();
        const errorElement = field.parentElement.querySelector('.error');

        for (const [rule, config] of Object.entries(rules)) {
            switch(rule) {
                case 'required':
                    if (!value) {
                        if (errorElement) errorElement.textContent = config.message;
                        field.classList.add('error-field');
                        return false;
                    }
                    break;
                case 'min':
                    if (value.length < config.value) {
                        if (errorElement) errorElement.textContent = config.message;
                        field.classList.add('error-field');
                        return false;
                    }
                    break;
                case 'max':
                    if (value.length > config.value) {
                        if (errorElement) errorElement.textContent = config.message;
                        field.classList.add('error-field');
                        return false;
                    }
                    break;
                case 'number':
                    if (isNaN(value) || value === '') {
                        if (errorElement) errorElement.textContent = config.message;
                        field.classList.add('error-field');
                        return false;
                    }
                    break;
                case 'range':
                    const num = parseFloat(value);
                    if (num < config.min || num > config.max) {
                        if (errorElement) errorElement.textContent = config.message;
                        field.classList.add('error-field');
                        return false;
                    }
                    break;
                case 'email':
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(value)) {
                        if (errorElement) errorElement.textContent = config.message;
                        field.classList.add('error-field');
                        return false;
                    }
                    break;
            }
        }

        field.classList.remove('error-field');
        if (errorElement) errorElement.textContent = '';
        return true;
    }
};

// ========== VALIDATION DU FORMULAIRE ==========
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("cancerForm");
    
    if (!form) return;

    const inputs = form.querySelectorAll('input, select');

    // Validation en temps réel
    inputs.forEach(input => {
        input.addEventListener('blur', () => {
            validateFormField(input);
        });

        input.addEventListener('input', () => {
            input.classList.remove('error-field');
            const errorElement = input.parentElement.querySelector('.error');
            if (errorElement) errorElement.textContent = '';
        });
    });

    // Validation BMI
    const bmiInput = document.getElementById("BMI");
    if (bmiInput) {
        bmiInput.addEventListener("input", validateBMI);
        bmiInput.addEventListener("blur", validateBMI);
    }

    // Affichage conditionnel des champs
    const ageSelect = document.getElementById("AgeCategory");
    if (ageSelect) {
        ageSelect.addEventListener("change", handleAgeChange);
        handleAgeChange();
    }

    // Soumission du formulaire
    form.addEventListener("submit", handleFormSubmit);
});

// Fonction pour valider un champ du formulaire
function validateFormField(field) {
    const value = field.value.trim();
    const fieldName = field.name || field.id;
    const errorElement = field.parentElement.querySelector('.error');

    if (fieldName === 'BMI') {
        const num = parseFloat(value);
        if (!value || isNaN(num) || num <= 0 || num > 200) {
            if (errorElement) {
                errorElement.textContent = "BMI doit être un nombre entre 1 et 200";
            }
            field.classList.add('error-field');
            return false;
        }
    }

    field.classList.remove('error-field');
    if (errorElement) errorElement.textContent = '';
    return true;
}

// Validation spécifique BMI
function validateBMI() {
    const bmiInput = document.getElementById("BMI");
    const bmiError = document.getElementById("bmiError");
    const value = parseFloat(bmiInput.value);

    if (isNaN(value) || value <= 0) {
        bmiError.textContent = "BMI doit être un nombre positif";
        bmiInput.classList.add('error-field');
        return false;
    } else if (value > 200) {
        bmiError.textContent = "BMI doit être inférieur à 200";
        bmiInput.classList.add('error-field');
        return false;
    } else {
        bmiError.textContent = "";
        bmiInput.classList.remove('error-field');
        return true;
    }
}

// Gestion du changement d'âge
function handleAgeChange() {
    const ageSelect = document.getElementById("AgeCategory");
    const diabeticGroup = document.getElementById("Diabetic")?.parentElement;
    
    if (!diabeticGroup) return;

    const ageText = ageSelect.value;
    const age = parseInt(ageText.split('-')[0]) || 80;
    
    if (age >= 50) {
        diabeticGroup.classList.remove('hidden');
        diabeticGroup.style.display = 'block';
    } else {
        diabeticGroup.classList.add('hidden');
        diabeticGroup.style.display = 'none';
        document.getElementById("Diabetic").value = "No";
    }
}

// Soumission du formulaire
async function handleFormSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const bmiInput = document.getElementById("BMI");

    // Validation finale
    if (!validateBMI()) {
        UI.showAlert("Veuillez corriger les erreurs du formulaire", 'danger');
        return;
    }

    const formData = new FormData(form);

    // Afficher le loader
    const loader = UI.showLoader("Analyse en cours...");
    form.appendChild(loader);

    // Mise à jour de la barre de progression
    UI.updateProgressBar(30);

    try {
        const response = await fetch(form.action || '/api/predict', {
            method: 'POST',
            body: formData
        });

        UI.updateProgressBar(70);

            if (response.ok) {
                const data = await response.json();
                console.debug('Prediction API response:', data);
                if (data.success) {
                    displayPredictionResult(data);
                    UI.showAlert("Prédiction réalisée avec succès!", 'success');
                } else {
                    UI.showAlert("Erreur: " + (data.error || "Erreur inconnue"), 'danger');
                }
            } else {
            const text = await response.text();
            console.error('Response:', text);
            UI.showAlert("Erreur serveur. Statut: " + response.status, 'danger');
        }

        UI.updateProgressBar(100);
        setTimeout(() => UI.updateProgressBar(0), 1000);

    } catch (error) {
        console.error('Erreur:', error);
        UI.showAlert("Erreur de connexion: " + error.message, 'danger');
        UI.updateProgressBar(0);
    } finally {
        UI.hideLoader();
    }
}

// Affichage du résultat de prédiction
function displayPredictionResult(data) {
    let resultContainer = document.querySelector('.result-container');
    
    if (!resultContainer) {
        resultContainer = document.createElement('div');
        resultContainer.className = 'result-container';
        document.querySelector('.container').appendChild(resultContainer);
    }

    const prediction = data.prediction || 'Inconnu';
    const probability = data.probability ? (data.probability * 100).toFixed(2) : 'N/A';
    
    const resultClass = prediction === 1 || prediction === 'Yes' ? 'prediction-positive' : 'prediction-negative';
    const resultText = prediction === 1 || prediction === 'Yes' ? '⚠️ RISQUE DÉTECTÉ' : '✓ AUCUN RISQUE';

    resultContainer.innerHTML = `
        <div class="result-title">📊 Résultat de la Prédiction</div>
        <div class="prediction-result ${resultClass}">
            ${resultText}
        </div>
        <div class="prediction-probability">
            <strong>Confiance:</strong> ${probability}%
        </div>
    `;

    // If explanation with SHAP values is present, render an interactive Plotly bar chart
    try {
            const expl = data.explanation;
            const explContainerId = 'explanation-block';
            // Create or reuse explanation block
            let explBlock = document.getElementById(explContainerId);
            if (!explBlock) {
                explBlock = document.createElement('div');
                explBlock.id = explContainerId;
                explBlock.style.marginTop = '12px';
                explBlock.style.padding = '12px';
                explBlock.style.background = '#fff7ed';
                explBlock.style.borderRadius = '8px';
                explBlock.style.borderLeft = '4px solid #f6ad55';
                resultContainer.appendChild(explBlock);
            } else {
                explBlock.innerHTML = '';
            }

            if (!expl) {
                explBlock.innerHTML = '<div style="color:#718096">Aucune explication fournie par le serveur.</div>';
                return;
            }

            if (expl.error) {
                explBlock.innerHTML = `<div style="color:#c53030; font-weight:600;">Erreur génération explication : ${expl.error}</div>`;
                // show raw JSON to help debugging
                const pre = document.createElement('pre');
                pre.textContent = JSON.stringify(expl, null, 2);
                pre.style.marginTop = '8px';
                pre.style.maxHeight = '180px';
                pre.style.overflow = 'auto';
                explBlock.appendChild(pre);
                return;
            }

            // Show base value and top features textual summary
            const baseHtml = `<div style="font-weight:700; margin-bottom:8px;">🧭 Explication (XAI) — Top contributions</div>` +
                (expl.base_value !== undefined && expl.base_value !== null ? `<div style="color:#4a5568; margin-bottom:8px;">Base value: ${expl.base_value.toFixed ? expl.base_value.toFixed(3) : expl.base_value}</div>` : '');
            explBlock.innerHTML = baseHtml;

            if (expl.top_features && Array.isArray(expl.top_features)) {
                const ul = document.createElement('ul');
                ul.style.margin = '0';
                ul.style.paddingLeft = '18px';
                ul.style.color = '#2d3748';
                expl.top_features.forEach(item => {
                    const li = document.createElement('li');
                    const sign = item.shap_value > 0 ? ' (augmente le risque)' : (item.shap_value < 0 ? ' (diminue le risque)' : ' (neutre)');
                    li.innerHTML = `<strong>${item.feature}</strong>: ${Number(item.shap_value).toFixed(3)}<span style="color:${item.shap_value>0? '#c53030':'#38a169'}">${sign}</span>`;
                    ul.appendChild(li);
                });
                explBlock.appendChild(ul);
            }

            // Render full SHAP bar chart if available
            if (expl.all_features && Array.isArray(expl.all_features) && window.Plotly) {
                const features = expl.all_features.map(item => item.feature);
                const shap_vals = expl.all_features.map(item => item.shap_value);

                const chartId = 'shap-chart';
                let chartDiv = document.getElementById(chartId);
                if (!chartDiv) {
                    chartDiv = document.createElement('div');
                    chartDiv.id = chartId;
                    chartDiv.style.marginTop = '12px';
                    chartDiv.style.height = '360px';
                    explBlock.appendChild(chartDiv);
                } else {
                    chartDiv.innerHTML = '';
                }

                const colors = shap_vals.map(v => (v >= 0 ? '#f56565' : '#38a169'));
                const trace = { x: shap_vals, y: features, orientation: 'h', type: 'bar', marker: { color: colors } };
                const layout = { margin: { l: 180, r: 40, t: 20, b: 40 }, xaxis: { title: 'SHAP value' }, yaxis: { automargin: true, autorange: 'reversed' } };
                Plotly.newPlot(chartDiv, [trace], layout, { responsive: true });
            }
    } catch (err) {
        console.error('Erreur rendu SHAP:', err);
    }

    resultContainer.scrollIntoView({ behavior: 'smooth' });

    // Add professional 'Generate report' button
    try {
        let reportBtn = document.getElementById('generate-report-btn');
        if (!reportBtn) {
            reportBtn = document.createElement('button');
            reportBtn.id = 'generate-report-btn';
            reportBtn.textContent = '📄 Générer le rapport détaillé (PDF)';
            reportBtn.className = 'btn-submit';
            reportBtn.style.marginTop = '12px';
            reportBtn.style.background = 'linear-gradient(135deg,#667eea 0%,#764ba2 100%)';
            reportBtn.style.color = '#fff';
            reportBtn.style.border = 'none';
            reportBtn.style.padding = '10px 16px';
            reportBtn.style.borderRadius = '8px';
            reportBtn.style.cursor = 'pointer';
            resultContainer.appendChild(reportBtn);

            reportBtn.addEventListener('click', async () => {
                reportBtn.disabled = true;
                reportBtn.textContent = 'Génération en cours...';
                const form = document.getElementById('cancerForm');
                const formData = new FormData(form);
                try {
                    const resp = await fetch('/report', { method: 'POST', body: formData });
                    if (resp.ok) {
                        const blob = await resp.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'xai_report.pdf';
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        window.URL.revokeObjectURL(url);
                    } else {
                        const text = await resp.text();
                        UI.showAlert('Erreur génération rapport: ' + text, 'danger');
                    }
                } catch (e) {
                    UI.showAlert('Erreur lors du téléchargement du rapport: ' + e.message, 'danger');
                } finally {
                    reportBtn.disabled = false;
                    reportBtn.textContent = '📄 Générer le rapport détaillé (PDF)';
                }
            });
        }
    } catch (err) {
        console.error('Erreur bouton rapport:', err);
    }
}

// ========== ANIMATIONS ==========
// Ajouter des animations au chargement
window.addEventListener('load', () => {
    document.querySelectorAll('.form-group').forEach((group, index) => {
        group.style.animationDelay = `${index * 0.1}s`;
    });
});

// ========== UTILITAIRES SUPPLÉMENTAIRES ==========
// Désactiver/activer le formulaire
function disableForm(form, disabled = true) {
    form.querySelectorAll('input, select, button').forEach(el => {
        el.disabled = disabled;
    });
}

// Réinitialiser le formulaire
function resetFormWithConfirmation(form) {
    if (confirm('Êtes-vous sûr de vouloir réinitialiser le formulaire?')) {
        form.reset();
        UI.showAlert("Formulaire réinitialisé", 'info', 3000);
    }
}

// Export des fonctions pour utilisation globale
window.UI = UI;
window.disableForm = disableForm;
window.resetFormWithConfirmation = resetFormWithConfirmation;
