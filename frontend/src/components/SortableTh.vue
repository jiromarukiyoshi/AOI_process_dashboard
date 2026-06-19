<template>
  <th
    class="sticky top-0 z-10 h-[70px] cursor-pointer select-none border-b border-r border-[#cbd6e2] bg-[#eaf0f6] px-4 py-3 text-center text-[22px] font-bold text-[#071d3a]"
    scope="col"
    @click="$emit('sort', column)"
  >
    <span class="inline-flex items-center justify-center gap-2 whitespace-nowrap">
      {{ label }}
      <span class="min-w-[16px] text-[16px] text-[#2563eb]">{{ marker }}</span>
    </span>
  </th>
</template>

<script setup>
import { computed } from "vue"


const props = defineProps({
  label: {
    type: String,
    required: true,
  },
  column: {
    type: String,
    required: true,
  },
  sortState: {
    type: Object,
    required: true,
  },
})

defineEmits(["sort"])

const marker = computed(() => {
  if (props.sortState.column !== props.column) return ""
  return props.sortState.direction === "asc" ? "▲" : "▼"
})
</script>

