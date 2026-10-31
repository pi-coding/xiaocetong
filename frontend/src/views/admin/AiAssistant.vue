<template>
  <div class="admin-ai">
    <section class="hero">
      <div>
        <h2>AI 运营助手</h2>
        <p>{{ insight?.summary || '正在汇总运营数据…' }}</p>
      </div>
      <el-button :icon="Refresh" size="small" :loading="loading" @click="loadInsight">刷新洞察</el-button>
    </section>

    <section class="grid">
      <div class="page-card chat-card">
        <div class="card-head">
          <h3>对话问答</h3>
          <span class="muted">基于实时数据，离线可用</span>
        </div>
        <ChatPanel
          scene="admin"
          welcome="你好，我是运营助手。可以问我：超时预警、待派单、员工绩效、统计数据、差评情况。"
          :questions="questions"
          placeholder="例如：现在有多少待派单？"
        />
      </div>

      <div class="page-card insights">
        <div class="card-head">
          <h3>智能洞察</h3>
          <span class="muted">{{ insight?.generated_at ? formatTime(insight.generated_at) : '' }}</span>
        </div>
        <div v-loading="loading" class="insight-list">
          <div v-for="item in insight?.insights || []" :key="item.title" class="insight" :class="item.level">
            <div class="insight-head">
              <span class="dot"></span>
              <strong>{{ item.title }}</strong>
            </div>
            <p class="detail">{{ item.detail }}</p>
            <el-button link type="primary" size="small" @click="router.push(item.path)">去处理</el-button>
          </div>
          <el-empty v-if="!loading && !(insight?.insights || []).length" description="暂无异常，运营状态良好" :image-size="70" />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import ChatPanel from '@/components/ChatPanel.vue'
import { fetchInsight } from '@/api/ai'
import { formatTime } from '@/utils/dict'

const router = useRouter()
const insight = ref(null)
const loading = ref(false)

const questions = ['有哪些超时预警', '现在有多少待派单', '员工绩效怎么样', '最近有差评吗', '今日运营数据']

const loadInsight = async () => {
  loading.value = true
  try {
    insight.value = await fetchInsight()
  } finally {
    loading.value = false
  }
}

onMounted(loadInsight)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.admin-ai {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 22px;
  border-radius: $cct-radius;
  color: #fff;
  background: linear-gradient(135deg, #0d3f47 0%, #0f7c80 60%, #12b8b6 100%);
  box-shadow: 0 10px 24px rgba(15, 87, 96, 0.22);

  h2 {
    margin: 0 0 6px;
    font-size: 19px;
  }

  p {
    margin: 0;
    font-size: 12px;
    opacity: 0.88;
    line-height: 1.6;
  }

  .el-button {
    background: rgba(255, 255, 255, 0.16);
    border: 1px solid rgba(255, 255, 255, 0.35);
    color: #fff;
    flex-shrink: 0;
  }
}

.grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 16px;
  min-height: 520px;
}

.chat-card {
  display: flex;
  flex-direction: column;
  min-height: 520px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;

  h3 {
    margin: 0;
    font-size: 15px;
  }

  .muted {
    font-size: 11px;
  }
}

.insights {
  display: flex;
  flex-direction: column;
}

.insight-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 200px;
}

.insight {
  padding: 12px 14px;
  border-radius: 12px;
  background: #f7fafb;
  border-left: 3px solid #9aa8b0;

  &.danger {
    border-left-color: $cct-danger;
    background: #fdf4f4;
  }

  &.warning {
    border-left-color: $cct-warning;
    background: #fdf9ef;
  }

  &.success {
    border-left-color: #22c55e;
    background: #f3faf5;
  }

  &.info {
    border-left-color: $cct-primary;
    background: #f2fafa;
  }
}

.insight-head {
  display: flex;
  align-items: center;
  gap: 6px;

  strong {
    font-size: 13px;
  }
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.55;
}

.detail {
  margin: 6px 0 4px;
  font-size: 12px;
  line-height: 1.6;
  color: #5c6f78;
}

@media (max-width: 1100px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>