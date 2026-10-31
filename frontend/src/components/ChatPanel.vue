<template>
  <div class="chat-panel">
    <div ref="listEl" class="messages">
      <div v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
        <div v-if="message.role === 'assistant'" class="avatar">
          <el-icon :size="16"><MagicStick /></el-icon>
        </div>
        <div class="bubble">
          <p class="text">{{ message.text }}</p>
          <div v-if="message.actions?.length" class="actions">
            <el-button
              v-for="action in message.actions"
              :key="action.path"
              size="small"
              type="primary"
              plain
              @click="go(action)"
            >
              {{ action.label }}
            </el-button>
          </div>
        </div>
      </div>

      <div v-if="thinking" class="message assistant">
        <div class="avatar"><el-icon :size="16"><MagicStick /></el-icon></div>
        <div class="bubble typing">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <div class="quick">
      <el-tag
        v-for="question in questions"
        :key="question"
        size="small"
        effect="plain"
        class="quick-tag"
        @click="ask(question)"
      >
        {{ question }}
      </el-tag>
    </div>

    <div class="composer">
      <el-input
        v-model="input"
        :placeholder="placeholder"
        maxlength="500"
        @keyup.enter="send"
      />
      <el-button type="primary" :loading="thinking" @click="send">发送</el-button>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import { chatWithAi } from '@/api/ai'

const props = defineProps({
  scene: { type: String, default: 'student' },
  welcome: { type: String, default: '你好，我是校厕通助手，有什么可以帮你？' },
  questions: { type: Array, default: () => [] },
  placeholder: { type: String, default: '输入你的问题…' },
})

const router = useRouter()
const messages = ref([{ role: 'assistant', text: props.welcome, actions: [] }])
const input = ref('')
const thinking = ref(false)
const listEl = ref(null)

const scrollToBottom = () => {
  nextTick(() => {
    if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
  })
}

const ask = (question) => {
  input.value = question
  send()
}

const send = async () => {
  const text = input.value.trim()
  if (!text || thinking.value) return

  messages.value.push({ role: 'user', text })
  input.value = ''
  thinking.value = true
  scrollToBottom()

  try {
    const data = await chatWithAi({ message: text, scene: props.scene })
    messages.value.push({ role: 'assistant', text: data.answer, actions: data.actions || [] })
  } catch {
    messages.value.push({
      role: 'assistant',
      text: '抱歉，助手暂时无法回答，请稍后再试。',
      actions: [],
    })
  } finally {
    thinking.value = false
    scrollToBottom()
  }
}

const go = (action) => router.push(action.path)
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 4px 2px 12px;
  min-height: 180px;
}

.message {
  display: flex;
  gap: 8px;

  &.user {
    justify-content: flex-end;

    .bubble {
      background: linear-gradient(135deg, $cct-primary, #12b8b6);
      color: #fff;
      border-radius: 14px 14px 4px 14px;
    }
  }

  &.assistant .bubble {
    background: #f4f9f9;
    border-radius: 14px 14px 14px 4px;
  }
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #e6f7f6;
  color: $cct-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.bubble {
  max-width: 86%;
  padding: 10px 12px;
}

.text {
  margin: 0;
  font-size: 13px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;

  .el-button {
    margin-left: 0;
  }
}

.typing {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 14px 16px;

  span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #9fc9c8;
    animation: blink 1.2s infinite ease-in-out;
  }

  span:nth-child(2) {
    animation-delay: 0.2s;
  }

  span:nth-child(3) {
    animation-delay: 0.4s;
  }
}

@keyframes blink {
  0%,
  80%,
  100% {
    opacity: 0.25;
    transform: translateY(0);
  }
  40% {
    opacity: 1;
    transform: translateY(-3px);
  }
}

.quick {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 10px 0;
  border-top: 1px dashed $cct-border;
}

.quick-tag {
  cursor: pointer;

  &:hover {
    color: $cct-primary;
    border-color: $cct-primary;
  }
}

.composer {
  display: flex;
  gap: 8px;
  padding-top: 4px;
}
</style>