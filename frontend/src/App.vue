<script setup>
import {
  Activity,
  BadgeCheck,
  BrainCircuit,
  CheckCircle2,
  Database,
  FlaskConical,
  Gauge,
  GitBranch,
  Layers,
  Loader2,
  Play,
  RefreshCw,
  Send,
  Sparkles,
  Trophy,
  UserRound,
} from 'lucide-vue-next'
import { computed, onMounted, reactive, ref } from 'vue'
import { api } from './api'

const layers = [
  { id: 'intake', label: 'Knowledge Intake', icon: Database },
  { id: 'intelligence', label: 'Knowledge Intelligence', icon: BrainCircuit },
  { id: 'generation', label: 'Interaction Generation', icon: FlaskConical },
  { id: 'evolution', label: 'Evolution', icon: GitBranch },
  { id: 'growth', label: 'User Growth', icon: UserRound },
]

const activeLayer = ref('intake')
const loading = ref(false)
const error = ref('')
const selectedChoice = ref('')
const activeInteraction = ref(null)
const summary = ref(null)
const sources = ref([])
const interactions = ref([])
const result = ref(null)

const form = reactive({
  title: 'Customer Escalation Review',
  domain: 'customer support',
  tags: 'support, escalation, operations',
  template: 'decision_scenario',
  content:
    'A useful escalation review separates customer impact, triggering event, missed signals, decision owner, and follow-up control. Teams should avoid marking an escalation complete until the root cause and prevention action are both documented.',
})

const feedback = reactive({
  completed: true,
  liked: true,
  reported: false,
  quality: 5,
  time_seconds: 180,
})

const selectedStep = computed(() => activeInteraction.value?.draft?.steps?.[0] || null)
const recentExtraction = computed(() => result.value?.source?.extraction || sources.value.find((s) => s.extraction)?.extraction)
const knowledgeUnits = computed(() => result.value?.units || recentExtraction.value?.units || [])
const topScore = computed(() => interactions.value[0]?.score || 0)
const completionRate = computed(() => {
  const plays = interactions.value.reduce((sum, item) => sum + item.plays, 0)
  const completions = interactions.value.reduce((sum, item) => sum + item.completions, 0)
  return plays ? Math.round((completions / plays) * 100) : 0
})

async function refresh() {
  const [summaryData, sourceData, interactionData] = await Promise.all([
    api.summary(),
    api.sources(),
    api.interactions(),
  ])
  summary.value = summaryData
  sources.value = sourceData
  interactions.value = interactionData
  if (!activeInteraction.value && interactionData.length) {
    activeInteraction.value = interactionData[0]
  }
}

async function runFullChain(nextLayer = 'intelligence') {
  loading.value = true
  error.value = ''
  selectedChoice.value = ''
  try {
    const payload = {
      title: form.title,
      content: form.content,
      domain: form.domain || 'general',
      tags: form.tags
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean),
      template: form.template,
    }
    result.value = await api.fullChain(payload)
    activeInteraction.value = result.value.interaction
    activeLayer.value = nextLayer
    await refresh()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function sendFeedback() {
  if (!activeInteraction.value) return
  loading.value = true
  error.value = ''
  try {
    activeInteraction.value = await api.submitFeedback({
      interaction_id: activeInteraction.value.id,
      completed: feedback.completed,
      liked: feedback.liked,
      reported: feedback.reported,
      quality: Number(feedback.quality),
      time_seconds: Number(feedback.time_seconds),
    })
    activeLayer.value = 'evolution'
    await refresh()
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function chooseInteraction(interaction) {
  activeInteraction.value = interaction
  selectedChoice.value = ''
  activeLayer.value = 'generation'
}

onMounted(async () => {
  try {
    await refresh()
  } catch (err) {
    error.value = err.message
  }
})
</script>

<template>
  <main class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <Layers :size="22" />
        <div>
          <strong>Knowledge AI</strong>
          <span>Evolution Platform</span>
        </div>
      </div>

      <nav class="layer-nav">
        <button
          v-for="layer in layers"
          :key="layer.id"
          type="button"
          :class="{ active: activeLayer === layer.id }"
          @click="activeLayer = layer.id"
        >
          <component :is="layer.icon" :size="18" />
          <span>{{ layer.label }}</span>
        </button>
      </nav>

      <button class="refresh-button" type="button" title="Refresh workspace" @click="refresh">
        <RefreshCw :size="17" />
        Refresh
      </button>
    </aside>

    <section class="page">
      <header class="topbar">
        <div>
          <p class="eyebrow">AI-native workspace</p>
          <h1>{{ layers.find((layer) => layer.id === activeLayer)?.label }}</h1>
        </div>
        <div class="status-pill">
          <Activity :size="16" />
          {{ summary?.total_feedback || 0 }} signals
        </div>
      </header>

      <section class="metrics" v-if="summary">
        <div class="metric">
          <Database :size="18" />
          <span>Sources</span>
          <strong>{{ summary.total_sources }}</strong>
        </div>
        <div class="metric">
          <Sparkles :size="18" />
          <span>Units</span>
          <strong>{{ summary.total_units }}</strong>
        </div>
        <div class="metric">
          <FlaskConical :size="18" />
          <span>Interactions</span>
          <strong>{{ summary.total_interactions }}</strong>
        </div>
        <div class="metric">
          <Trophy :size="18" />
          <span>Top score</span>
          <strong>{{ topScore }}</strong>
        </div>
      </section>

      <p v-if="error" class="error">{{ error }}</p>

      <section v-if="activeLayer === 'intake'" class="layer-grid intake-grid">
        <div class="panel">
          <div class="panel-title">
            <Send :size="18" />
            <h2>Knowledge Collection</h2>
          </div>
          <label>
            Title
            <input v-model="form.title" />
          </label>
          <div class="two-col">
            <label>
              Domain
              <input v-model="form.domain" />
            </label>
            <label>
              Template
              <select v-model="form.template">
                <option value="decision_scenario">Decision</option>
                <option value="risk_triage">Risk triage</option>
                <option value="flash_review">Flash review</option>
                <option value="incident_reconstruction">Reconstruction</option>
              </select>
            </label>
          </div>
          <label>
            Tags
            <input v-model="form.tags" />
          </label>
          <label>
            Source content
            <textarea v-model="form.content" rows="13" />
          </label>
          <button class="primary" type="button" :disabled="loading" @click="runFullChain('intelligence')">
            <Loader2 v-if="loading" class="spin" :size="17" />
            <Play v-else :size="17" />
            Store in MinIO and extract
          </button>
        </div>

        <div class="panel">
          <div class="panel-title">
            <Database :size="18" />
            <h2>Collected Sources</h2>
          </div>
          <div class="source-list">
            <article v-for="source in sources" :key="source.id">
              <strong>{{ source.title }}</strong>
              <span>{{ source.domain }} · {{ source.status }}</span>
              <small v-if="source.object_key">MinIO: {{ source.object_bucket }}/{{ source.object_key }}</small>
              <small v-else>Object storage pending</small>
            </article>
          </div>
        </div>
      </section>

      <section v-if="activeLayer === 'intelligence'" class="layer-grid">
        <div class="panel wide">
          <div class="panel-title">
            <BrainCircuit :size="18" />
            <h2>Knowledge Intelligence</h2>
          </div>
          <div v-if="knowledgeUnits.length" class="unit-grid">
            <article v-for="unit in knowledgeUnits" :key="unit.title" class="unit-card">
              <div class="unit-head">
                <strong>{{ unit.title }}</strong>
                <span>{{ unit.difficulty }}</span>
              </div>
              <p>{{ unit.summary }}</p>
              <div class="tag-row">
                <span>{{ unit.unit_type }}</span>
                <span v-for="tag in unit.tags" :key="tag">{{ tag }}</span>
              </div>
            </article>
          </div>
          <div v-else class="empty-state">
            <BrainCircuit :size="22" />
            <span>No extracted units yet.</span>
          </div>
        </div>

        <div class="panel">
          <div class="panel-title">
            <BadgeCheck :size="18" />
            <h2>Extraction Record</h2>
          </div>
          <p class="objective">{{ recentExtraction?.source_summary || 'Run the intake layer to extract structure.' }}</p>
          <button class="primary compact" type="button" :disabled="!knowledgeUnits.length" @click="activeLayer = 'generation'">
            Continue to generation
          </button>
        </div>
      </section>

      <section v-if="activeLayer === 'generation'" class="layer-grid">
        <div class="panel player wide">
          <div class="panel-title">
            <FlaskConical :size="18" />
            <h2>Interaction Player</h2>
          </div>
          <template v-if="activeInteraction && selectedStep">
            <div class="interaction-head">
              <div>
                <p class="eyebrow">{{ activeInteraction.draft.template }}</p>
                <h3>{{ activeInteraction.draft.title }}</h3>
              </div>
              <strong class="score">{{ activeInteraction.score }}</strong>
            </div>
            <p class="objective">{{ activeInteraction.draft.objective }}</p>
            <p class="prompt">{{ selectedStep.prompt }}</p>
            <div class="choice-list">
              <button
                v-for="choice in selectedStep.choices"
                :key="choice.id"
                type="button"
                :class="{ selected: selectedChoice === choice.id, correct: selectedChoice === choice.id && choice.is_correct }"
                @click="selectedChoice = choice.id"
              >
                <CheckCircle2 v-if="selectedChoice === choice.id && choice.is_correct" :size="18" />
                <span>{{ choice.label }}</span>
              </button>
            </div>
            <p v-if="selectedChoice" class="feedback-text">
              {{ selectedStep.choices.find((choice) => choice.id === selectedChoice)?.feedback }}
            </p>
            <div class="feedback-bar">
              <label>
                Quality
                <input v-model="feedback.quality" min="1" max="5" type="range" />
              </label>
              <label class="check">
                <input v-model="feedback.completed" type="checkbox" />
                Completed
              </label>
              <label class="check">
                <input v-model="feedback.liked" type="checkbox" />
                Liked
              </label>
              <button class="primary compact" type="button" :disabled="loading" @click="sendFeedback">
                <Gauge :size="17" />
                Submit signal
              </button>
            </div>
          </template>
          <div v-else class="empty-state">
            <FlaskConical :size="22" />
            <span>No interaction selected.</span>
          </div>
        </div>

        <div class="panel">
          <div class="panel-title">
            <Sparkles :size="18" />
            <h2>Generated Items</h2>
          </div>
          <div class="rank-list">
            <button v-for="interaction in interactions" :key="interaction.id" type="button" @click="chooseInteraction(interaction)">
              <span>{{ interaction.draft.title }}</span>
              <strong>{{ interaction.score }}</strong>
              <small>{{ interaction.draft.difficulty }} · {{ interaction.draft.estimated_minutes }} min</small>
            </button>
          </div>
        </div>
      </section>

      <section v-if="activeLayer === 'evolution'" class="layer-grid">
        <div class="panel wide">
          <div class="panel-title">
            <GitBranch :size="18" />
            <h2>Evolution Ranking</h2>
          </div>
          <div class="rank-list">
            <button
              v-for="interaction in interactions"
              :key="interaction.id"
              type="button"
              :class="{ active: activeInteraction?.id === interaction.id }"
              @click="chooseInteraction(interaction)"
            >
              <span>{{ interaction.draft.title }}</span>
              <strong>{{ interaction.score }}</strong>
              <small>{{ interaction.plays }} plays · {{ interaction.likes }} likes · {{ interaction.avg_quality.toFixed(1) }} quality</small>
            </button>
          </div>
        </div>
        <div class="panel">
          <div class="panel-title">
            <Activity :size="18" />
            <h2>Signal Health</h2>
          </div>
          <div class="stat-stack">
            <strong>{{ summary?.total_feedback || 0 }}</strong><span>Total feedback</span>
            <strong>{{ completionRate }}%</strong><span>Completion rate</span>
            <strong>{{ topScore }}</strong><span>Leading score</span>
          </div>
        </div>
      </section>

      <section v-if="activeLayer === 'growth'" class="layer-grid">
        <div class="panel wide">
          <div class="panel-title">
            <UserRound :size="18" />
            <h2>User Growth</h2>
          </div>
          <div class="growth-grid">
            <div class="growth-tile"><strong>Explorer</strong><span>Current level</span></div>
            <div class="growth-tile"><strong>{{ summary?.total_feedback || 0 }}</strong><span>Practice signals</span></div>
            <div class="growth-tile"><strong>{{ completionRate }}%</strong><span>Completion discipline</span></div>
            <div class="growth-tile"><strong>{{ knowledgeUnits.length }}</strong><span>Active knowledge units</span></div>
          </div>
        </div>
        <div class="panel">
          <div class="panel-title">
            <Trophy :size="18" />
            <h2>Achievements</h2>
          </div>
          <div class="tag-row achievement-row">
            <span>First source</span>
            <span>Extractor</span>
            <span>Scenario player</span>
            <span>Signal contributor</span>
          </div>
        </div>
      </section>
    </section>
  </main>
</template>
