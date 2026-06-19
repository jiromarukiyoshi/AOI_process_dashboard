<template>
  <div class="grid min-h-[96px] grid-cols-[1fr_auto_auto] items-center gap-5 rounded-[14px] border border-[#d3dce6] bg-white px-6 py-5 shadow-sm">
    <div class="text-[27px] font-bold text-[#071d3a]">{{ title }}</div>
    <div class="whitespace-nowrap text-[25px] font-bold text-[#071d3a]">
      {{ summary.done }} / {{ summary.total }} 店舗
    </div>
    <div class="min-w-[94px] text-right text-[36px] font-black leading-none text-[#2457e6]">
      {{ summary.rate }}%
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true,
  },
  summary: {
    type: Object,
    default: () => ({ done: 0, total: 0, rate: 0 }),
  },
})
</script>

