<template>
  <div class="image-upload">
    <div v-for="(url, index) in modelValue" :key="`${url}-${index}`" class="thumb">
      <img :src="url" alt="上传图片" />
      <button type="button" class="remove" @click="remove(index)">
        <el-icon :size="12"><Close /></el-icon>
      </button>
    </div>

    <button
      v-if="modelValue.length < limit"
      type="button"
      class="add"
      :disabled="uploading"
      @click="openPicker"
    >
      <el-icon v-if="!uploading" :size="20"><Plus /></el-icon>
      <span v-else class="uploading">上传中</span>
    </button>

    <input ref="picker" type="file" accept="image/*" hidden @change="onChoose" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadImage } from '@/api/files'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  limit: { type: Number, default: 3 },
})
const emit = defineEmits(['update:modelValue'])

const picker = ref(null)
const uploading = ref(false)

const openPicker = () => picker.value?.click()

const onChoose = async (event) => {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.warning('图片不能超过 5MB')
    return
  }
  uploading.value = true
  try {
    const data = await uploadImage(file)
    emit('update:modelValue', [...props.modelValue, data.url])
  } finally {
    uploading.value = false
  }
}

const remove = (index) => {
  emit(
    'update:modelValue',
    props.modelValue.filter((_, idx) => idx !== index),
  )
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.image-upload {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.thumb,
.add {
  width: 76px;
  height: 76px;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
}

.thumb {
  border: 1px solid $cct-border;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
}

.remove {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 18px;
  height: 18px;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.add {
  border: 1px dashed #c8d6da;
  background: #fafcfc;
  color: $cct-text-light;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;

  &:hover {
    border-color: $cct-primary;
    color: $cct-primary;
  }

  &:disabled {
    cursor: not-allowed;
  }
}

.uploading {
  font-size: 11px;
}
</style>