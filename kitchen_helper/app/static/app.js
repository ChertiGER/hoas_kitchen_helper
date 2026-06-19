// Globale Statusvariablen
let allRecipes = [];
let calendars = [];
let todoLists = [];
let currentModalRecipe = null;
let currentModalServings = 4;
let lastGeneratedRecipe = null;
let defaultCalendarEntity = "";
let defaultTodoEntity = "";
let activeFilterTags = [];
let uploadedImageB64 = null;
let uploadedImageMime = null;

// Initialisierung bei Laden der Seite
document.addEventListener("DOMContentLoaded", () => {
    // Standardmäßig leeres Rezeptformular vorbereiten
    resetRecipeForm();
    
    // Daten laden
    loadRecipes();
    loadSystemStatus();
    loadPantry();
    
    // Heutiges Datum als Standardwert für den Kalenderplaner eintragen
    const today = new Date().toISOString().split('T')[0];
    document.getElementById("modal-plan-date").value = today;
});

// ---- NAVIGATION & TAB SCHALTUNG ----
function switchTab(tabId) {
    // Alle Tab-Inhalte ausblenden
    document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
    document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("block"));
    
    // Gewählten Tab einblenden
    const activeTab = document.getElementById(tabId);
    if (activeTab) {
        activeTab.classList.remove("hidden");
        activeTab.classList.add("block");
    }
    
    // Tab-Buttons aktualisieren
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.classList.remove("bg-amber-500", "text-slate-950", "shadow-sm");
        btn.classList.add("text-slate-400", "hover:text-white");
    });
    
    const activeBtn = document.getElementById(`btn-${tabId}`);
    if (activeBtn) {
        activeBtn.classList.remove("text-slate-400", "hover:text-white");
        activeBtn.classList.add("bg-amber-500", "text-slate-950", "shadow-sm");
    }

    // Wenn der Rezept-Tab geöffnet wird, Rezepte neu laden
    if (tabId === "recipes-tab") {
        loadRecipes();
    }
}

// ---- TOAST ALERTS SYSTEM ----
function showAlert(message, type = "info") {
    const container = document.getElementById("alert-container");
    const alertId = "alert-" + Date.now();
    
    let bgClass = "bg-slate-900 border-slate-700 text-slate-100";
    let icon = '<i class="fa-solid fa-circle-info text-blue-400"></i>';
    
    if (type === "success") {
        bgClass = "bg-emerald-950 border-emerald-800 text-emerald-100";
        icon = '<i class="fa-solid fa-circle-check text-emerald-400"></i>';
    } else if (type === "error") {
        bgClass = "bg-red-950 border-red-800 text-red-100";
        icon = '<i class="fa-solid fa-circle-exclamation text-red-400"></i>';
    }
    
    const alertHtml = `
        <div id="${alertId}" class="flex items-center gap-3 px-4 py-3.5 rounded-xl border ${bgClass} shadow-xl pointer-events-auto transition-all duration-300 transform translate-x-12 opacity-0">
            <div class="text-lg shrink-0">${icon}</div>
            <div class="text-xs font-medium">${message}</div>
            <button onclick="document.getElementById('${alertId}').remove()" class="ml-auto text-slate-400 hover:text-white transition">
                <i class="fa-solid fa-xmark text-xs"></i>
            </button>
        </div>
    `;
    
    container.insertAdjacentHTML("beforeend", alertHtml);
    const alertElement = document.getElementById(alertId);
    
    // Animation Einblenden
    setTimeout(() => {
        alertElement.classList.remove("translate-x-12", "opacity-0");
    }, 50);
    
    // Nach 4 Sekunden ausblenden und löschen
    setTimeout(() => {
        if (alertElement) {
            alertElement.classList.add("translate-x-12", "opacity-0");
            setTimeout(() => alertElement.remove(), 300);
        }
    }, 4500);
}

// ---- REZEPTFORMULAR STEUERUNG (MANUELL) ----
function addIngredientRow(name = "", amount = "", unit = "") {
    const container = document.getElementById("ingredients-container");
    const rowId = "ing-row-" + Date.now() + "-" + Math.random().toString(36).substr(2, 4);
    
    const rowHtml = `
        <div id="${rowId}" class="ingredient-row grid grid-cols-12 gap-2 items-center bg-slate-950/60 p-2 rounded-xl border border-slate-800/80">
            <div class="col-span-6 sm:col-span-5">
                <input type="text" placeholder="Zutat (z.B. Mehl)" value="${name}" required class="ing-name bg-slate-950 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-800 text-xs w-full focus:outline-none focus:border-amber-500">
            </div>
            <div class="col-span-3">
                <input type="number" step="any" placeholder="Menge" value="${amount}" class="ing-amount bg-slate-950 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-800 text-xs w-full focus:outline-none focus:border-amber-500">
            </div>
            <div class="col-span-3 sm:col-span-3">
                <input type="text" placeholder="Einheit (g, EL)" value="${unit}" class="ing-unit bg-slate-950 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-800 text-xs w-full focus:outline-none focus:border-amber-500">
            </div>
            <div class="col-span-12 sm:col-span-1 flex justify-end">
                <button type="button" onclick="document.getElementById('${rowId}').remove()" class="text-red-400 hover:text-red-300 p-1.5 hover:bg-red-500/10 rounded-lg transition-all border border-transparent hover:border-red-500/10">
                    <i class="fa-solid fa-trash text-xs"></i>
                </button>
            </div>
        </div>
    `;
    container.insertAdjacentHTML("beforeend", rowHtml);
}

function resetRecipeForm() {
    document.getElementById("recipe-form").reset();
    document.getElementById("form-recipe-id").value = "";
    document.getElementById("form-title").innerHTML = '<i class="fa-solid fa-plus text-amber-500"></i> Neues Rezept anlegen';
    
    // Tags Checkboxen zurücksetzen
    document.querySelectorAll(".form-tag-checkbox").forEach(cb => cb.checked = false);
    
    const container = document.getElementById("ingredients-container");
    container.innerHTML = "";
    
    // Mit 3 leeren Zeilen starten
    addIngredientRow();
    addIngredientRow();
    addIngredientRow();
}

// ---- REZEPT SPEICHERN ----
async function saveRecipe(event) {
    event.preventDefault();
    
    const recipeId = document.getElementById("form-recipe-id").value;
    const title = document.getElementById("form-title-input").value;
    const servings = parseInt(document.getElementById("form-servings").value) || 4;
    const description = document.getElementById("form-description").value;
    const instructions = document.getElementById("form-instructions").value;
    
    // Tags sammeln
    const tags = [];
    document.querySelectorAll(".form-tag-checkbox:checked").forEach(cb => {
        tags.push(cb.value);
    });
    
    // Zutaten sammeln
    const ingredients = [];
    const rows = document.querySelectorAll(".ingredient-row");
    
    rows.forEach(row => {
        const name = row.querySelector(".ing-name").value.trim();
        const amountVal = row.querySelector(".ing-amount").value.trim();
        const unit = row.querySelector(".ing-unit").value.trim();
        
        if (name) {
            let amount = null;
            if (amountVal !== "") {
                amount = parseFloat(amountVal);
            }
            ingredients.push({ name, amount, unit });
        }
    });
    
    if (ingredients.length === 0) {
        showAlert("Bitte füge mindestens eine Zutat hinzu.", "error");
        return;
    }
    
    const payload = {
        title,
        description,
        servings,
        instructions,
        ingredients,
        tags,
        source: recipeId ? undefined : "Manuell" // Behalte alte Quelle bei Updates bei
    };
    
    try {
        let response;
        if (recipeId) {
            // Update
            response = await fetch(`./api/recipes/${recipeId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        } else {
            // Create
            response = await fetch("./api/recipes", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        }
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Serverfehler beim Speichern des Rezepts");
        }
        
        showAlert(recipeId ? "Rezept erfolgreich aktualisiert!" : "Rezept erfolgreich gespeichert!", "success");
        resetRecipeForm();
        switchTab("recipes-tab");
    } catch (e) {
        showAlert(e.message, "error");
    }
}

// ---- REZEPTE LADEN & GRID ANZEIGEN ----
async function loadRecipes() {
    const search = document.getElementById("recipe-search").value;
    const grid = document.getElementById("recipe-grid");
    
    try {
        let url = "./api/recipes";
        if (search) {
            url += `?search=${encodeURIComponent(search)}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) throw new Error("Fehler beim Abrufen der Rezepte");
        
        allRecipes = await response.json();
        
        if (allRecipes.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full py-16 flex flex-col items-center justify-center text-slate-500 text-center space-y-3">
                    <div class="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-lg">
                        <i class="fa-solid fa-carrot"></i>
                    </div>
                    <div>
                        <p class="font-bold text-white text-sm">Keine Rezepte gefunden</p>
                        <p class="text-xs text-slate-400 mt-1">Lege manuell ein neues Rezept an oder nutze den KI-Chefkoch!</p>
                    </div>
                </div>
            `;
            return;
        }

        // Clientseitige Filterung nach Tags
        let filteredRecipes = allRecipes;
        if (activeFilterTags.length > 0) {
            filteredRecipes = allRecipes.filter(recipe => {
                return activeFilterTags.every(t => recipe.tags && recipe.tags.includes(t));
            });
        }

        if (filteredRecipes.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full py-16 flex flex-col items-center justify-center text-slate-500 text-center space-y-3">
                    <div class="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-lg">
                        <i class="fa-solid fa-filter"></i>
                    </div>
                    <div>
                        <p class="font-bold text-white text-sm">Keine Treffer</p>
                        <p class="text-xs text-slate-400 mt-1">Für die ausgewählten Filter-Kombinationen wurden keine Rezepte gefunden.</p>
                    </div>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = filteredRecipes.map(recipe => {
            const isAi = recipe.source === "KI-generiert" || recipe.source?.startsWith("Importiert") || recipe.source === "Bild-Scan" || recipe.source === "Visuelle Resteverwertung";
            const sourceTag = isAi 
                ? `<span class="bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md"><i class="fa-solid fa-sparkles mr-0.5"></i> ${recipe.source}</span>`
                : '<span class="bg-slate-800 border border-slate-700 text-slate-400 text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md">Manuell</span>';

            const tagsHtml = recipe.tags && recipe.tags.length > 0
                ? recipe.tags.map(t => `<span class="bg-slate-950 text-amber-500/80 text-[9px] font-semibold px-2 py-0.5 rounded border border-slate-800/80">${t}</span>`).join("")
                : "";

            return `
                <div onclick="openRecipeModal(${recipe.id})" class="bg-slate-900 rounded-2xl border border-slate-800/80 shadow-md p-5 hover:border-amber-500/40 hover:shadow-lg transition-all duration-300 cursor-pointer flex flex-col justify-between h-full group">
                    <div class="space-y-3">
                        <div class="flex items-center justify-between gap-2">
                            ${sourceTag}
                            <span class="text-slate-500 text-xs font-semibold flex items-center gap-1">
                                <i class="fa-solid fa-users"></i> ${recipe.servings} Port.
                            </span>
                        </div>
                        <div>
                            <h3 class="text-white font-extrabold group-hover:text-amber-400 transition-colors text-lg line-clamp-1">${recipe.title}</h3>
                            <p class="text-slate-400 text-xs mt-1.5 line-clamp-2 leading-relaxed">${recipe.description || 'Keine Beschreibung hinterlegt.'}</p>
                        </div>
                        <div class="flex flex-wrap gap-1 pt-1">
                            ${tagsHtml}
                        </div>
                    </div>
                    
                    <div class="pt-4 border-t border-slate-800/85 mt-4 flex items-center justify-between">
                        <span class="text-[11px] text-slate-500 font-medium">
                            <i class="fa-solid fa-basket-shopping text-amber-500/70 mr-1"></i> ${recipe.ingredients.length} Zutaten
                        </span>
                        <span class="text-amber-500 font-bold text-xs group-hover:translate-x-1 transition-transform flex items-center gap-1">
                            Ansehen <i class="fa-solid fa-arrow-right text-[10px]"></i>
                        </span>
                    </div>
                </div>
            `;
        }).join("");
        
    } catch (e) {
        grid.innerHTML = `<div class="col-span-full text-center text-red-400 py-12"><i class="fa-solid fa-triangle-exclamation mr-1.5"></i> ${e.message}</div>`;
    }
}

// ---- REZEPT DETAILED MODAL STEUERUNG ----
async function openRecipeModal(recipeId) {
    try {
        const response = await fetch(`./api/recipes/${recipeId}`);
        if (!response.ok) throw new Error("Rezept konnte nicht geladen werden.");
        
        currentModalRecipe = await response.json();
        currentModalServings = currentModalRecipe.servings;
        
        // Modal-Elemente befüllen
        document.getElementById("modal-title").innerText = currentModalRecipe.title;
        document.getElementById("modal-description").innerText = currentModalRecipe.description || "Keine Beschreibung hinterlegt.";
        
        // Tags anzeigen
        const tagsContainer = document.getElementById("modal-tags-display");
        if (currentModalRecipe.tags && currentModalRecipe.tags.length > 0) {
            tagsContainer.innerHTML = currentModalRecipe.tags.map(t => `<span class="bg-slate-950 text-amber-500 text-[10px] font-bold px-2.5 py-0.5 rounded border border-slate-800">${t}</span>`).join("");
            tagsContainer.classList.remove("hidden");
        } else {
            tagsContainer.innerHTML = "";
            tagsContainer.classList.add("hidden");
        }
        
        const tag = document.getElementById("modal-tag");
        const isAi = currentModalRecipe.source === "KI-generiert" || currentModalRecipe.source?.startsWith("Importiert") || currentModalRecipe.source === "Bild-Scan" || currentModalRecipe.source === "Visuelle Resteverwertung";
        tag.innerText = currentModalRecipe.source || "Rezept";
        if (isAi) {
            tag.className = "text-[10px] font-black uppercase tracking-widest px-2.5 py-0.5 rounded-full border border-amber-500/20 bg-amber-500/10 text-amber-400";
        } else {
            tag.className = "text-[10px] font-black uppercase tracking-widest px-2.5 py-0.5 rounded-full border border-slate-700 bg-slate-800 text-slate-400";
        }
        
        document.getElementById("modal-servings-display").innerText = currentModalServings;
        document.getElementById("modal-instructions").innerText = currentModalRecipe.instructions;
        
        // Button zurücksetzen
        const toggleBtn = document.getElementById("btn-toggle-all-ingredients");
        toggleBtn.innerText = "Alle abwählen";
        
        // Zutaten rendern (mit Skalierung = 1.0 zu Beginn)
        renderModalIngredients();
        
        // Datum im Kalenderplaner immer auf heute aktualisieren
        document.getElementById("modal-plan-date").value = new Date().toISOString().split('T')[0];
        
        // Modal anzeigen
        document.getElementById("recipe-modal").classList.remove("hidden");
    } catch (e) {
        showAlert(e.message, "error");
    }
}

function closeRecipeModal() {
    document.getElementById("recipe-modal").classList.add("hidden");
    currentModalRecipe = null;
}

// ---- INTERAKTIVES PORTIONIEREN IM MODAL ----
function adjustModalServings(change) {
    if (!currentModalRecipe) return;
    
    const newServings = currentModalServings + change;
    if (newServings < 1) return;
    
    currentModalServings = newServings;
    document.getElementById("modal-servings-display").innerText = currentModalServings;
    
    // Zutatenliste mit neuer Skalierung neu rendern
    renderModalIngredients();
}

function renderModalIngredients() {
    if (!currentModalRecipe) return;
    
    const list = document.getElementById("modal-ingredients-list");
    const originalServings = currentModalRecipe.servings;
    const scale = currentModalServings / originalServings;
    
    list.innerHTML = currentModalRecipe.ingredients.map((ing, idx) => {
        let amountText = "";
        let finalAmount = null;
        
        if (ing.amount !== null) {
            finalAmount = ing.amount * scale;
            if (Number.isInteger(finalAmount)) {
                amountText = intToGermanFraction(finalAmount);
            } else {
                amountText = parseFloat(finalAmount.toFixed(2)).toString();
            }
        }
        
        const unitText = ing.unit ? ` ${ing.unit}` : "";
        const formattedAmountString = amountText ? `<span class="font-extrabold text-white text-xs">${amountText}${unitText}</span>` : `<span class="font-bold text-slate-400 text-xs">${ing.unit || ''}</span>`;
        
        const isAlwaysAtHome = ing.always_at_home === true;
        const checkboxChecked = isAlwaysAtHome ? "" : "checked";
        const opacityClass = isAlwaysAtHome ? "opacity-50 hover:opacity-100 transition-opacity" : "";
        const badgeHtml = isAlwaysAtHome ? `<span class="text-[9px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.5 rounded font-bold ml-1">Vorrat</span>` : "";
        
        return `
            <label class="flex items-center gap-3 py-1.5 px-2 rounded-lg hover:bg-slate-900 cursor-pointer border border-transparent hover:border-slate-800 transition ${opacityClass}">
                <input type="checkbox" ${checkboxChecked} class="modal-ing-checkbox rounded border-slate-700 bg-slate-950 text-amber-500 focus:ring-amber-500 w-4 h-4" 
                    data-name="${ing.name}" 
                    data-amount="${finalAmount || ''}" 
                    data-unit="${ing.unit || ''}">
                <div class="text-xs flex items-center gap-1.5 select-none w-full justify-between">
                    <span class="text-slate-300 font-medium flex items-center gap-1">
                        ${ing.name}
                        ${badgeHtml}
                    </span>
                    ${formattedAmountString}
                </div>
            </label>
        `;
    }).join("");
}

function intToGermanFraction(val) {
    // Einfache Rückgabe als String ohne Nachkommastellen bei Integers
    return val.toString();
}

function toggleAllIngredientsCheckbox() {
    const checkboxes = document.querySelectorAll(".modal-ing-checkbox");
    const toggleBtn = document.getElementById("btn-toggle-all-ingredients");
    
    // Prüfen, ob aktuell alle oder einige ausgewählt sind
    const someChecked = Array.from(checkboxes).some(cb => cb.checked);
    
    checkboxes.forEach(cb => {
        cb.checked = !someChecked;
    });
    
    toggleBtn.innerText = someChecked ? "Alle auswählen" : "Alle abwählen";
}

// ---- EINKAUFSLISTEN INTEGRATION ----
async function sendCheckedToShoppingList() {
    const checkboxes = document.querySelectorAll(".modal-ing-checkbox:checked");
    if (checkboxes.length === 0) {
        showAlert("Wähle mindestens eine Zutat aus, die du auf die Einkaufsliste setzen willst.", "error");
        return;
    }
    
    const todoEntity = document.getElementById("modal-todo-select").value;
    if (!todoEntity) {
        showAlert("Bitte wähle eine Einkaufsliste aus.", "error");
        return;
    }
    
    // Formatiere jede Zutat für die HA-Einkaufsliste
    const items = [];
    checkboxes.forEach(cb => {
        const name = cb.getAttribute("data-name");
        const amount = cb.getAttribute("data-amount");
        const unit = cb.getAttribute("data-unit");
        
        let itemString = "";
        if (amount) {
            itemString = `${amount}${unit ? ' ' + unit : ''} ${name}`;
        } else if (unit) {
            itemString = `${unit} ${name}`;
        } else {
            itemString = name;
        }
        items.push(itemString);
    });
    
    try {
        const response = await fetch("./api/ha/shopping-list-add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                todo_entity: todoEntity,
                items: items
            })
        });
        
        if (!response.ok) throw new Error("Fehler beim Übermitteln an Home Assistant");
        
        const result = await response.json();
        showAlert(`<i class="fa-solid fa-basket-shopping"></i> ${result.message}`, "success");
    } catch (e) {
        showAlert(`Konnte Zutaten nicht hinzufügen: ${e.message}`, "error");
    }
}

// ---- KALENDERPLANER INTEGRATION ----
async function planRecipeInCalendar() {
    if (!currentModalRecipe) return;
    
    const calendarEntity = document.getElementById("modal-calendar-select").value;
    const date = document.getElementById("modal-plan-date").value;
    
    if (!calendarEntity) {
        showAlert("Bitte wähle einen Kalender aus.", "error");
        return;
    }
    
    if (!date) {
        showAlert("Bitte wähle ein Datum aus.", "error");
        return;
    }
    
    try {
        const response = await fetch("./api/ha/calendar-plan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                calendar_entity: calendarEntity,
                recipe_id: currentModalRecipe.id,
                date: date,
                servings: currentModalServings
            })
        });
        
        if (!response.ok) throw new Error("Konnte den Kalendereintrag nicht anlegen.");
        
        showAlert(`<i class="fa-solid fa-calendar-check text-indigo-400"></i> Rezept erfolgreich für den ${date} eingeplant!`, "success");
    } catch (e) {
        showAlert(e.message, "error");
    }
}

// ---- RECIPE EDIT & DELETE FROM DETAIL MODAL ----
function deleteRecipeFromModal() {
    if (!currentModalRecipe) return;
    
    if (confirm(`Möchtest du das Rezept "${currentModalRecipe.title}" wirklich unwiderruflich löschen?`)) {
        const id = currentModalRecipe.id;
        fetch(`./api/recipes/${id}`, { method: "DELETE" })
            .then(res => {
                if (!res.ok) throw new Error("Löschen fehlgeschlagen");
                showAlert("Rezept erfolgreich gelöscht.", "success");
                closeRecipeModal();
                loadRecipes();
            })
            .catch(e => showAlert(e.message, "error"));
    }
}

function editRecipeFromModal() {
    if (!currentModalRecipe) return;
    
    const recipe = currentModalRecipe;
    closeRecipeModal();
    
    // Formular befüllen
    document.getElementById("form-recipe-id").value = recipe.id;
    document.getElementById("form-title-input").value = recipe.title;
    document.getElementById("form-servings").value = recipe.servings;
    document.getElementById("form-description").value = recipe.description || "";
    document.getElementById("form-instructions").value = recipe.instructions;
    
    // Tags Checkboxen befüllen
    document.querySelectorAll(".form-tag-checkbox").forEach(cb => {
        cb.checked = recipe.tags && recipe.tags.includes(cb.value);
    });
    
    document.getElementById("form-title").innerHTML = `<i class="fa-solid fa-pen-to-square text-amber-500"></i> Rezept "${recipe.title}" bearbeiten`;
    
    const container = document.getElementById("ingredients-container");
    container.innerHTML = "";
    
    recipe.ingredients.forEach(ing => {
        addIngredientRow(ing.name, ing.amount !== null ? ing.amount : "", ing.unit || "");
    });
    
    // Tab wechseln
    switchTab("add-tab");
}

// ---- KI-REZEPT GENERIERUNG ----
async function generateRecipe() {
    const prompt = document.getElementById("ai-prompt").value.trim();
    const dietary = document.getElementById("ai-dietary").value;
    const style = document.getElementById("ai-style").value;
    const servings = parseInt(document.getElementById("ai-servings").value) || 4;
    
    if (!prompt) {
        showAlert("Bitte gib eine Idee oder Zutaten für die KI ein.", "error");
        return;
    }
    
    const btn = document.getElementById("btn-generate-ai");
    const emptyState = document.getElementById("ai-output-empty");
    const loader = document.getElementById("ai-output-loader");
    const resultCard = document.getElementById("ai-output-result");
    
    // UI in Ladezustand versetzen
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generiere Rezept...';
    emptyState.classList.add("hidden");
    resultCard.classList.add("hidden");
    loader.classList.remove("hidden");
    
    try {
        const response = await fetch("./api/recipes/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt, dietary, style, servings })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Fehler bei der Rezeptgenerierung");
        }
        
        lastGeneratedRecipe = await response.json();
        
        // Ergebnis befüllen
        document.getElementById("ai-result-title").innerText = lastGeneratedRecipe.title;
        document.getElementById("ai-result-desc").innerText = lastGeneratedRecipe.description || "";
        document.getElementById("ai-result-servings").innerText = lastGeneratedRecipe.servings;
        document.getElementById("ai-result-instructions").innerText = lastGeneratedRecipe.instructions;
        
        const ingredientsList = document.getElementById("ai-result-ingredients");
        ingredientsList.innerHTML = lastGeneratedRecipe.ingredients.map(ing => {
            const amountText = ing.amount !== null ? `${ing.amount} ` : "";
            const unitText = ing.unit ? `${ing.unit} ` : "";
            return `
                <li class="flex items-center gap-2 border-b border-slate-800/60 py-1.5">
                    <span class="w-1.5 h-1.5 bg-amber-500 rounded-full"></span>
                    <span>${amountText}${unitText}<strong>${ing.name}</strong></span>
                </li>
            `;
        }).join("");
        
        // Ergebnis anzeigen
        loader.classList.add("hidden");
        resultCard.classList.remove("hidden");
        showAlert("<i class=\"fa-solid fa-wand-magic-sparkles text-amber-400\"></i> Rezept wurde erfolgreich generiert!", "success");
    } catch (e) {
        showAlert(e.message, "error");
        loader.classList.add("hidden");
        emptyState.classList.remove("hidden");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-sparkles"></i> Rezept generieren';
    }
}

async function saveAiRecipeDirectly() {
    if (!lastGeneratedRecipe) return;
    
    try {
        const response = await fetch("./api/recipes", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(lastGeneratedRecipe)
        });
        
        if (!response.ok) throw new Error("Konnte das KI-Rezept nicht abspeichern.");
        
        showAlert(`KI-Rezept "${lastGeneratedRecipe.title}" wurde erfolgreich gespeichert!`, "success");
        lastGeneratedRecipe = null;
        
        // Zurücksetzen der KI-Oberfläche
        document.getElementById("ai-prompt").value = "";
        document.getElementById("ai-output-result").classList.add("hidden");
        document.getElementById("ai-output-empty").classList.remove("hidden");
        
        // Wechsle zu Rezepten
        switchTab("recipes-tab");
    } catch (e) {
        showAlert(e.message, "error");
    }
}

function editAiRecipeBeforeSaving() {
    if (!lastGeneratedRecipe) return;
    
    const recipe = lastGeneratedRecipe;
    
    // Wechsle zu Hinzufügen-Tab und befülle Formular
    document.getElementById("form-recipe-id").value = "";
    document.getElementById("form-title-input").value = recipe.title;
    document.getElementById("form-servings").value = recipe.servings;
    document.getElementById("form-description").value = recipe.description || "";
    document.getElementById("form-instructions").value = recipe.instructions;
    
    // Tags Checkboxen befüllen
    document.querySelectorAll(".form-tag-checkbox").forEach(cb => {
        cb.checked = recipe.tags && recipe.tags.includes(cb.value);
    });
    
    document.getElementById("form-title").innerHTML = `<i class="fa-solid fa-wand-magic-sparkles text-amber-500"></i> KI-Entwurf bearbeiten`;
    
    const container = document.getElementById("ingredients-container");
    container.innerHTML = "";
    
    recipe.ingredients.forEach(ing => {
        addIngredientRow(ing.name, ing.amount !== null ? ing.amount : "", ing.unit || "");
    });
    
    // Letztes KI-Rezept wegschmeißen da im Editor geladen
    lastGeneratedRecipe = null;
    document.getElementById("ai-prompt").value = "";
    document.getElementById("ai-output-result").classList.add("hidden");
    document.getElementById("ai-output-empty").classList.remove("hidden");
    
    switchTab("add-tab");
}

// ---- HOME ASSISTANT STATUS & DROPDOWNS BEFÜLLEN ----
async function loadSystemStatus() {
    try {
        // HA Status & Verbindung abfragen
        const response = await fetch("./api/ha/status");
        if (!response.ok) throw new Error("Verbindung zum Küchenhelfer-Backend gestört.");
        
        const status = await response.json();
        
        defaultCalendarEntity = status.default_calendar || "";
        defaultTodoEntity = status.default_shopping_list || "";
        
        const statusIcon = document.getElementById("ha-status-icon");
        const statusText = document.getElementById("ha-status-text");
        const tokenText = document.getElementById("ha-token-text");
        
        if (status.connected) {
            statusIcon.className = "w-12 h-12 rounded-xl flex items-center justify-center text-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
            statusIcon.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
            statusText.innerText = "Verbunden (HA Core API)";
            statusText.className = "text-sm font-bold text-emerald-400";
        } else {
            statusIcon.className = "w-12 h-12 rounded-xl flex items-center justify-center text-xl bg-red-500/10 text-red-400 border border-red-500/20";
            statusIcon.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
            statusText.innerText = "Offline / Kein Zugriff";
            statusText.className = "text-sm font-bold text-red-400";
        }
        
        if (status.using_token) {
            tokenText.innerText = "Aktiviert & Validiert";
            tokenText.className = "text-sm font-bold text-emerald-400";
        } else {
            tokenText.innerText = "Inaktiv (Entwicklungs-Mock)";
            tokenText.className = "text-sm font-bold text-amber-500";
        }
        
        // Kalender laden
        const calRes = await fetch("./api/ha/calendars");
        if (calRes.ok) {
            calendars = await calRes.json();
            populateCalendarsDropdowns();
        }
        
        // To-Do-Listen laden
        const todoRes = await fetch("./api/ha/todo-lists");
        if (todoRes.ok) {
            todoLists = await todoRes.json();
            populateTodoDropdowns();
        }
        
    } catch (e) {
        console.error("Fehler beim Laden des HA-Status:", e);
    }
}

function populateCalendarsDropdowns() {
    const listContainer = document.getElementById("settings-calendars-list");
    const modalSelect = document.getElementById("modal-calendar-select");
    const settingsSelect = document.getElementById("settings-calendar-select");
    
    if (calendars.length === 0) {
        listContainer.innerHTML = '<p class="text-slate-500 text-sm p-2">Keine Kalender gefunden.</p>';
        modalSelect.innerHTML = '<option value="">Kein Kalender verfügbar</option>';
        settingsSelect.innerHTML = '<option value="">Kein Kalender verfügbar</option>';
        return;
    }
    
    // Status-Tab Liste
    listContainer.innerHTML = calendars.map(cal => `
        <div class="flex items-center justify-between py-1.5 px-2.5 rounded-lg bg-slate-900/50 text-xs border border-slate-800/50">
            <span class="text-slate-300 font-bold">${cal.name}</span>
            <span class="text-slate-500 font-mono">${cal.entity_id}</span>
        </div>
    `).join("");
    
    // Dropdowns befüllen
    const calOptionsHtml = calendars.map(cal => `
        <option value="${cal.entity_id}">${cal.name}</option>
    `).join("");
    
    modalSelect.innerHTML = calOptionsHtml;
    settingsSelect.innerHTML = `<option value="">-- Kein Standard --</option>` + calOptionsHtml;

    if (defaultCalendarEntity && calendars.some(cal => cal.entity_id === defaultCalendarEntity)) {
        modalSelect.value = defaultCalendarEntity;
        settingsSelect.value = defaultCalendarEntity;
    } else {
        settingsSelect.value = "";
    }
}

function populateTodoDropdowns() {
    const listContainer = document.getElementById("settings-todos-list");
    const modalSelect = document.getElementById("modal-todo-select");
    const defaultSelect = document.getElementById("default-todo-select");
    const settingsSelect = document.getElementById("settings-todo-select");
    
    // Füge die klassische Home Assistant Einkaufsliste immer als Fallback hinzu
    const allOptions = [...todoLists, { entity_id: "legacy", name: "Klassische Einkaufsliste (shopping_list)" }];
    
    // Status-Tab Liste
    listContainer.innerHTML = allOptions.map(todo => `
        <div class="flex items-center justify-between py-1.5 px-2.5 rounded-lg bg-slate-900/50 text-xs border border-slate-800/50">
            <span class="text-slate-300 font-bold">${todo.name}</span>
            <span class="text-slate-500 font-mono">${todo.entity_id}</span>
        </div>
    `).join("");
    
    // Dropdowns befüllen
    const selectHtml = allOptions.map(todo => `
        <option value="${todo.entity_id}">${todo.name}</option>
    `).join("");
    
    modalSelect.innerHTML = selectHtml;
    defaultSelect.innerHTML = selectHtml;
    settingsSelect.innerHTML = `<option value="">-- Kein Standard --</option>` + selectHtml;
    
    // Standardwert für defaultSelect/modalSelect/settingsSelect setzen
    if (defaultTodoEntity && allOptions.some(o => o.entity_id === defaultTodoEntity)) {
        defaultSelect.value = defaultTodoEntity;
        modalSelect.value = defaultTodoEntity;
        settingsSelect.value = defaultTodoEntity;
    } else {
        settingsSelect.value = "";
        const hasShoppingList = allOptions.find(o => o.entity_id === "todo.shopping_list");
        if (hasShoppingList) {
            defaultSelect.value = "todo.shopping_list";
            modalSelect.value = "todo.shopping_list";
        } else {
            defaultSelect.value = "legacy";
            modalSelect.value = "legacy";
        }
    }
    
    // Wenn defaultSelect geändert wird, ändere auch den Wert in den anderen Dropdowns und speichere
    defaultSelect.addEventListener("change", (e) => {
        modalSelect.value = e.target.value;
        settingsSelect.value = e.target.value;
        defaultTodoEntity = e.target.value;
        saveConfigSettingsSilently();
    });
}

// ---- PANTRY / STANDARDVORRAT VERWALTUNG ----
let pantryItems = [];

async function loadPantry() {
    try {
        const response = await fetch("./api/pantry");
        if (!response.ok) throw new Error("Fehler beim Laden des Standardvorrats");
        pantryItems = await response.json();
        renderPantryList();
    } catch (e) {
        console.error("Fehler beim Laden der Pantry:", e);
    }
}

function renderPantryList() {
    const list = document.getElementById("pantry-list");
    if (!list) return;
    
    if (pantryItems.length === 0) {
        list.innerHTML = '<p class="text-slate-500 text-xs p-2">Keine eigenen Standardzutaten definiert.</p>';
        return;
    }
    
    list.innerHTML = pantryItems.map(item => `
        <div class="flex items-center justify-between py-1.5 px-2.5 rounded-lg bg-slate-900/50 text-xs border border-slate-800/50">
            <span class="text-slate-300 font-semibold">${item}</span>
            <button onclick="deletePantryItem('${item.replace(/'/g, "\\'")}')" class="text-red-400 hover:text-red-300 p-1 hover:bg-red-500/10 rounded transition-all">
                <i class="fa-solid fa-trash-can"></i>
            </button>
        </div>
    `).join("");
}

async function addPantryItem() {
    const input = document.getElementById("pantry-input");
    const name = input.value.trim();
    if (!name) return;
    
    try {
        const response = await fetch("./api/pantry", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Konnte Zutat nicht hinzufügen");
        }
        
        input.value = "";
        showAlert(`"${name}" zum Standardvorrat hinzugefügt.`, "success");
        await loadPantry();
    } catch (e) {
        showAlert(e.message, "error");
    }
}

async function deletePantryItem(name) {
    try {
        const response = await fetch(`./api/pantry?name=${encodeURIComponent(name)}`, {
            method: "DELETE"
        });
        
        if (!response.ok) throw new Error("Fehler beim Löschen");
        
        showAlert(`"${name}" aus dem Standardvorrat entfernt.`, "success");
        await loadPantry();
    } catch (e) {
        showAlert(e.message, "error");
    }
}

async function saveConfigSettings() {
    const calendar = document.getElementById("settings-calendar-select").value;
    const todo = document.getElementById("settings-todo-select").value;
    
    try {
        const response = await fetch("./api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                default_calendar: calendar,
                default_shopping_list: todo
            })
        });
        
        if (!response.ok) throw new Error("Fehler beim Speichern der Einstellungen");
        
        defaultCalendarEntity = calendar;
        defaultTodoEntity = todo;
        
        // Sync recipes tab select & modal select
        const defaultSelect = document.getElementById("default-todo-select");
        if (defaultSelect && todo) defaultSelect.value = todo;
        const modalTodoSelect = document.getElementById("modal-todo-select");
        if (modalTodoSelect && todo) modalTodoSelect.value = todo;
        const modalCalSelect = document.getElementById("modal-calendar-select");
        if (modalCalSelect && calendar) modalCalSelect.value = calendar;
        
        showAlert("Standard-Einstellungen erfolgreich gespeichert!", "success");
    } catch (e) {
        showAlert(e.message, "error");
    }
}

async function saveConfigSettingsSilently() {
    const calendar = document.getElementById("settings-calendar-select").value;
    const todo = document.getElementById("settings-todo-select").value;
    
    try {
        await fetch("./api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                default_calendar: calendar,
                default_shopping_list: todo
            })
        });
        defaultCalendarEntity = calendar;
        defaultTodoEntity = todo;
        
        const modalTodoSelect = document.getElementById("modal-todo-select");
        if (modalTodoSelect && todo) modalTodoSelect.value = todo;
        const modalCalSelect = document.getElementById("modal-calendar-select");
        if (modalCalSelect && calendar) modalCalSelect.value = calendar;
    } catch (e) {
        console.error("Fehler beim stillen Speichern der Einstellungen:", e);
    }
}

// ---- RECIPE TAG FILTERING ----
function toggleTagFilter(tag, button) {
    const idx = activeFilterTags.indexOf(tag);
    if (idx > -1) {
        // Tag entfernen
        activeFilterTags.splice(idx, 1);
        button.classList.remove("bg-amber-500", "text-slate-950", "border-amber-500/40");
        button.classList.add("bg-slate-950", "text-slate-400", "border-slate-850");
    } else {
        // Tag hinzufügen
        activeFilterTags.push(tag);
        button.classList.add("bg-amber-500", "text-slate-950", "border-amber-500/40");
        button.classList.remove("bg-slate-950", "text-slate-400", "border-slate-850");
    }
    loadRecipes();
}

function clearTagFilters() {
    activeFilterTags = [];
    document.querySelectorAll(".tag-filter-btn").forEach(btn => {
        btn.classList.remove("bg-amber-500", "text-slate-950", "border-amber-500/40");
        btn.classList.add("bg-slate-950", "text-slate-400", "border-slate-850");
    });
    loadRecipes();
}

// ---- AI SUB-MODE SWITCHER ----
function switchAiMode(modeId) {
    // Alle Sub-Modi ausblenden
    document.querySelectorAll(".ai-mode-content").forEach(el => {
        el.classList.add("hidden");
        el.classList.remove("block");
    });
    
    // Gewählten Sub-Modus einblenden
    const target = document.getElementById(`ai-${modeId}`);
    if (target) {
        target.classList.remove("hidden");
        target.classList.add("block");
    }
    
    // Buttons stylen
    document.querySelectorAll(".ai-mode-btn").forEach(btn => {
        btn.classList.remove("bg-amber-500", "text-slate-950", "shadow-sm");
        btn.classList.add("text-slate-400", "hover:text-white");
    });
    
    const activeBtn = document.getElementById(`btn-${modeId}`);
    if (activeBtn) {
        activeBtn.classList.remove("text-slate-400", "hover:text-white");
        activeBtn.classList.add("bg-amber-500", "text-slate-950", "shadow-sm");
    }
}
function compressAndResizeImage(file, maxWidth = 1200, maxHeight = 1200, quality = 0.7) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = function(e) {
            const img = new Image();
            img.onload = function() {
                let width = img.width;
                let height = img.height;
                
                if (width > height) {
                    if (width > maxWidth) {
                        height = Math.round((height * maxWidth) / width);
                        width = maxWidth;
                    }
                } else {
                    if (height > maxHeight) {
                        width = Math.round((width * maxHeight) / height);
                        height = maxHeight;
                    }
                }
                
                const canvas = document.createElement("canvas");
                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext("2d");
                ctx.drawImage(img, 0, 0, width, height);
                
                canvas.toBlob((blob) => {
                    if (blob) {
                        const newFileName = file.name.replace(/\.[^/.]+$/, "") + ".jpg";
                        const compressedFile = new File([blob], newFileName, {
                            type: "image/jpeg",
                            lastModified: Date.now()
                        });
                        resolve(compressedFile);
                    } else {
                        reject(new Error("Canvas conversion failed"));
                    }
                }, "image/jpeg", quality);
            };
            img.onerror = () => reject(new Error("Image load failed"));
            img.src = e.target.result;
        };
        reader.onerror = () => reject(new Error("File read failed"));
        reader.readAsDataURL(file);
    });
}

// ---- VISION / FOTO HANDLERS ----
function previewUploadedImage(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.type.startsWith("image/")) {
        showAlert("Bitte wähle eine gültige Bilddatei aus.", "error");
        return;
    }
    
    uploadedImageMime = file.type;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById("vision-image-preview");
        preview.src = e.target.result;
        
        document.getElementById("vision-upload-placeholder").classList.add("hidden");
        document.getElementById("vision-image-preview-container").classList.remove("hidden");
        
        uploadedImageB64 = e.target.result.split(",")[1];
    };
    reader.readAsDataURL(file);
}

function clearVisionImage(event) {
    if (event) event.stopPropagation();
    
    uploadedImageB64 = null;
    uploadedImageMime = null;
    
    document.getElementById("ai-image-file").value = "";
    document.getElementById("vision-image-preview").src = "";
    
    document.getElementById("vision-upload-placeholder").classList.remove("hidden");
    document.getElementById("vision-image-preview-container").classList.add("hidden");
}

// ---- SUB-MODE API CALLS ----
async function scrapeRecipeFromUrlBtn() {
    const url = document.getElementById("ai-scrape-url").value.trim();
    if (!url) {
        showAlert("Bitte gib eine gültige Rezept-URL ein.", "error");
        return;
    }
    
    const btn = document.getElementById("btn-scrape-ai");
    const emptyState = document.getElementById("ai-output-empty");
    const loader = document.getElementById("ai-output-loader");
    const resultCard = document.getElementById("ai-output-result");
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scrape Rezept...';
    emptyState.classList.add("hidden");
    resultCard.classList.add("hidden");
    loader.classList.remove("hidden");
    
    try {
        const response = await fetch("./api/recipes/scrape", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Fehler beim Scrapen");
        }
        
        lastGeneratedRecipe = await response.json();
        showGeneratedRecipeResult();
        document.getElementById("ai-scrape-url").value = "";
    } catch(e) {
        showAlert(e.message, "error");
        loader.classList.add("hidden");
        emptyState.classList.remove("hidden");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-download"></i> Rezept importieren';
    }
}

async function importRecipeImageBtn() {
    if (!uploadedImageB64) {
        showAlert("Bitte wähle zuerst ein Rezeptfoto aus.", "error");
        return;
    }
    
    const btn = document.getElementById("btn-vision-import");
    const emptyState = document.getElementById("ai-output-empty");
    const loader = document.getElementById("ai-output-loader");
    const resultCard = document.getElementById("ai-output-result");
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Lese Rezept...';
    emptyState.classList.add("hidden");
    resultCard.classList.add("hidden");
    loader.classList.remove("hidden");
    
    const fileInput = document.getElementById("ai-image-file");
    let fileToUpload = fileInput.files[0];
    
    try {
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Komprimiere Bild...';
        fileToUpload = await compressAndResizeImage(fileToUpload);
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Lese Rezept...';
    } catch (err) {
        console.warn("Client-side compression failed, uploading original:", err);
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Lese Rezept...';
    }
    
    const formData = new FormData();
    formData.append("file", fileToUpload);
    
    try {
        const response = await fetch("./api/recipes/import-image", {
            method: "POST",
            body: formData
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Fehler beim Einlesen des Bildes");
        }
        
        lastGeneratedRecipe = await response.json();
        showGeneratedRecipeResult();
        clearVisionImage();
    } catch(e) {
        showAlert(e.message, "error");
        loader.classList.add("hidden");
        emptyState.classList.remove("hidden");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-file-invoice"></i> Rezept einlesen';
    }
}

async function analyseLeftoversImageBtn() {
    if (!uploadedImageB64) {
        showAlert("Bitte wähle zuerst ein Foto deines Kühlschranks/Vorrats aus.", "error");
        return;
    }
    
    const btn = document.getElementById("btn-vision-leftovers");
    const emptyState = document.getElementById("ai-output-empty");
    const loader = document.getElementById("ai-output-loader");
    const resultCard = document.getElementById("ai-output-result");
    
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Suche Rezepte...';
    emptyState.classList.add("hidden");
    resultCard.classList.add("hidden");
    loader.classList.remove("hidden");
    
    const fileInput = document.getElementById("ai-image-file");
    let fileToUpload = fileInput.files[0];
    
    try {
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Komprimiere Bild...';
        fileToUpload = await compressAndResizeImage(fileToUpload);
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Suche Rezepte...';
    } catch (err) {
        console.warn("Client-side compression failed, uploading original:", err);
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Suche Rezepte...';
    }
    
    const formData = new FormData();
    formData.append("file", fileToUpload);
    
    try {
        const response = await fetch("./api/recipes/visual-leftovers", {
            method: "POST",
            body: formData
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Fehler bei der Resteverwertung");
        }
        
        lastGeneratedRecipe = await response.json();
        showGeneratedRecipeResult();
        clearVisionImage();
    } catch(e) {
        showAlert(e.message, "error");
        loader.classList.add("hidden");
        emptyState.classList.remove("hidden");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-carrot"></i> Resteverwertung';
    }
}

function showGeneratedRecipeResult() {
    const emptyState = document.getElementById("ai-output-empty");
    const loader = document.getElementById("ai-output-loader");
    const resultCard = document.getElementById("ai-output-result");
    
    document.getElementById("ai-result-title").innerText = lastGeneratedRecipe.title;
    document.getElementById("ai-result-desc").innerText = lastGeneratedRecipe.description || "";
    document.getElementById("ai-result-servings").innerText = lastGeneratedRecipe.servings;
    document.getElementById("ai-result-instructions").innerText = lastGeneratedRecipe.instructions;
    
    const ingredientsList = document.getElementById("ai-result-ingredients");
    ingredientsList.innerHTML = lastGeneratedRecipe.ingredients.map(ing => {
        const amountText = ing.amount !== null ? `${ing.amount} ` : "";
        const unitText = ing.unit ? `${ing.unit} ` : "";
        return `
            <li class="flex items-center gap-2 border-b border-slate-800/60 py-1.5">
                <span class="w-1.5 h-1.5 bg-amber-500 rounded-full"></span>
                <span>${amountText}${unitText}<strong>${ing.name}</strong></span>
            </li>
        `;
    }).join("");
    
    loader.classList.add("hidden");
    resultCard.classList.remove("hidden");
    showAlert("<i class=\"fa-solid fa-wand-magic-sparkles text-amber-400\"></i> Rezept geladen!", "success");
}
