const form = document.getElementById('planner-form');
const results = document.getElementById('results');

const activityFactor = {
  sedentario: 1.2,
  leve: 1.375,
  moderado: 1.55,
  alto: 1.725,
};

const goalConfig = {
  emagrecer: {
    calorieDelta: -450,
    proteinFactor: 2,
    fatFactor: 0.8,
    focus: 'Déficit calórico com treinos metabólicos e musculação para preservar massa magra.',
  },
  definir: {
    calorieDelta: -250,
    proteinFactor: 2.2,
    fatFactor: 0.85,
    focus: 'Controle calórico moderado para reduzir gordura e melhorar definição muscular.',
  },
  reeducacao: {
    calorieDelta: -150,
    proteinFactor: 1.8,
    fatFactor: 0.9,
    focus: 'Ajustes sustentáveis na alimentação e rotina ativa para evolução consistente.',
  },
};

const workoutTemplates = [
  'Treino A: membros inferiores + caminhada inclinada de 20 minutos',
  'Treino B: superiores + core + HIIT leve de 12 minutos',
  'Treino C: circuito funcional full body com 6 exercícios',
  'Treino D: cardio contínuo de 35 a 45 minutos + mobilidade',
  'Treino E: glúteos, posterior e abdômen + finalização aeróbica',
  'Treino F: superiores, postura e estabilidade de tronco',
  'Treino G: recuperação ativa com caminhada, alongamento e liberação miofascial',
];

const mealTemplates = {
  cafe: [
    'Iogurte natural ou vegetal + aveia + fruta + chia',
    'Omelete com legumes + 1 fatia de pão integral',
  ],
  almoco: [
    'Proteína magra, arroz integral ou batata-doce, feijão e salada colorida',
    'Bowl com frango/desfiado, quinoa, legumes assados e folhas',
  ],
  lanche: [
    'Shake proteico ou vitamina com fruta e pasta de amendoim',
    'Mix de castanhas + fruta de baixo índice glicêmico',
  ],
  jantar: [
    'Prato semelhante ao almoço em porção levemente menor',
    'Sopa com legumes, proteína e fio de azeite',
  ],
};

function calculatePlan(data) {
  const { weight, height, age, sex, activity, goal, days } = data;
  const bmr =
    sex === 'masculino'
      ? 10 * weight + 6.25 * height - 5 * age + 5
      : 10 * weight + 6.25 * height - 5 * age - 161;

  const tdee = bmr * activityFactor[activity];
  const config = goalConfig[goal];
  const targetCalories = Math.max(1200, Math.round(tdee + config.calorieDelta));
  const proteinGrams = Math.round(weight * config.proteinFactor);
  const fatGrams = Math.round(weight * config.fatFactor);
  const carbGrams = Math.max(80, Math.round((targetCalories - proteinGrams * 4 - fatGrams * 9) / 4));
  const bmi = (weight / ((height / 100) * (height / 100))).toFixed(1);

  return {
    bmi,
    tdee: Math.round(tdee),
    targetCalories,
    proteinGrams,
    fatGrams,
    carbGrams,
    focus: config.focus,
    workouts: buildWorkoutPlan(days, goal),
  };
}

function buildWorkoutPlan(days, goal) {
  const selected = workoutTemplates.slice(0, days);
  if (goal === 'emagrecer' && days < 7) {
    selected.push('Bônus: 8 a 10 mil passos por dia para aumentar o gasto energético.');
  }
  if (goal === 'definir') {
    selected.push('Priorize progressão de carga e execução controlada nos exercícios principais.');
  }
  if (goal === 'reeducacao') {
    selected.push('Inclua 2 pausas ativas de 10 minutos ao longo do dia para reduzir o sedentarismo.');
  }
  return selected;
}

function renderPlan(data, plan) {
  const restrictions = data.diet?.trim()
    ? `<p class="plan-text"><strong>Preferências/restrições:</strong> ${data.diet.trim()}.</p>`
    : '<p class="plan-text"><strong>Preferências/restrições:</strong> nenhuma informada.</p>';

  results.innerHTML = `
    <div class="section-heading">
      <p class="eyebrow">Plano de ${data.name}</p>
      <h2>${labelGoal(data.goal)} com estratégia personalizada</h2>
    </div>
    <div class="results-grid">
      <div class="metrics-grid">
        <article class="metric">
          <strong>${plan.bmi}</strong>
          <span>IMC estimado</span>
        </article>
        <article class="metric">
          <strong>${plan.targetCalories} kcal</strong>
          <span>Meta calórica diária</span>
        </article>
        <article class="metric">
          <strong>${plan.tdee} kcal</strong>
          <span>Gasto energético estimado</span>
        </article>
      </div>

      <article class="plan-block">
        <h3>Estratégia principal</h3>
        <p class="plan-text">${plan.focus}</p>
        ${restrictions}
      </article>

      <article class="plan-block">
        <h3>Macronutrientes diários</h3>
        <ul>
          <li><strong>Proteínas:</strong> ${plan.proteinGrams} g por dia.</li>
          <li><strong>Carboidratos:</strong> ${plan.carbGrams} g por dia.</li>
          <li><strong>Gorduras:</strong> ${plan.fatGrams} g por dia.</li>
          <li><strong>Hidratação:</strong> meta inicial de ${(data.weight * 35).toFixed(0)} ml de água por dia.</li>
        </ul>
      </article>

      <article class="plan-block">
        <h3>Sugestão de refeições</h3>
        <ul>
          <li><strong>Café da manhã:</strong> ${mealTemplates.cafe.join(' ou ')}.</li>
          <li><strong>Almoço:</strong> ${mealTemplates.almoco.join(' ou ')}.</li>
          <li><strong>Lanche:</strong> ${mealTemplates.lanche.join(' ou ')}.</li>
          <li><strong>Jantar:</strong> ${mealTemplates.jantar.join(' ou ')}.</li>
        </ul>
      </article>

      <article class="plan-block">
        <h3>Plano semanal de treinos</h3>
        <ul>
          ${plan.workouts.map((item) => `<li>${item}</li>`).join('')}
        </ul>
      </article>

      <p class="notice">
        Este app oferece uma sugestão inicial educativa. Para condições clínicas, dor, lesões,
        medicações ou ajustes finos de dieta, procure um nutricionista e um profissional de educação física.
      </p>
    </div>
  `;
}

function labelGoal(goal) {
  return {
    emagrecer: 'emagrecimento',
    definir: 'definição muscular',
    reeducacao: 'reeducação alimentar',
  }[goal];
}

form.addEventListener('submit', (event) => {
  event.preventDefault();

  const data = {
    name: document.getElementById('name').value.trim(),
    goal: document.getElementById('goal').value,
    weight: Number(document.getElementById('weight').value),
    height: Number(document.getElementById('height').value),
    age: Number(document.getElementById('age').value),
    sex: document.getElementById('sex').value,
    activity: document.getElementById('activity').value,
    days: Number(document.getElementById('days').value),
    diet: document.getElementById('diet').value,
  };

  const plan = calculatePlan(data);
  renderPlan(data, plan);
});
