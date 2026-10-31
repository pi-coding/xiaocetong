<template>
  <div ref="chartEl" class="echart" :style="{ height, width: '100%' }"></div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: String, default: '280px' },
})

const chartEl = ref(null)
let chart = null
let observer = null

const render = () => {
  if (chart) chart.setOption(props.option, true)
}

onMounted(() => {
  chart = echarts.init(chartEl.value)
  render()
  if (typeof ResizeObserver !== 'undefined') {
    observer = new ResizeObserver(() => chart?.resize())
    observer.observe(chartEl.value)
  }
})

watch(() => props.option, render, { deep: true })

onBeforeUnmount(() => {
  observer?.disconnect()
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.echart {
  min-height: 120px;
}
</style>