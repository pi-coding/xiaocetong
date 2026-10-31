<template>
  <div class="ai-page">
    <section class="hero">
      <div>
        <p class="greeting">AI 助手</p>
        <p class="sub">工单进度、报修引导、附近厕所、积分规则，问我即可</p>
      </div>
      <el-icon :size="32"><ChatDotRound /></el-icon>
    </section>

    <section class="page-card chat-card">
      <ChatPanel
        scene="student"
        welcome="你好，我是校厕通助手。可以问我：工单进度、厕所堵塞怎么办、附近哪有厕所、积分怎么获得。"
        :questions="questions"
        placeholder="例如：我的工单到哪了？"
      />
    </section>
  </div>
</template>

<script setup>
import ChatPanel from '@/components/ChatPanel.vue'

const questions = ['我的工单到哪了', '厕所堵了怎么办', '附近哪有厕所', '积分怎么获得', '多久打扫一次']
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.ai-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
  min-height: calc(100vh - 180px);
}

.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-radius: $cct-radius;
  color: #fff;
  background: linear-gradient(135deg, #0e7c80 0%, #12b8b6 100%);
  flex-shrink: 0;
}

.greeting {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
}

.sub {
  margin: 5px 0 0;
  font-size: 12px;
  opacity: 0.85;
}

.chat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 420px;
  padding-bottom: 14px;
}
</style>