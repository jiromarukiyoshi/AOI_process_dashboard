<template>
  <div class="flex h-full flex-col bg-[#f2f5f8] p-7 text-[#071d3a]">
    <header class="flex min-h-[96px] shrink-0 items-center justify-between gap-6 rounded-[14px] border border-[#d3dce6] bg-white px-6 py-4 shadow-sm">
      <div class="min-w-0">
        <h1 class="truncate text-[34px] font-bold leading-tight">AOI長泉倉庫進捗ダッシュボード</h1>
      </div>
      <div class="flex shrink-0 items-center gap-4 text-[23px]">
        <label for="shipDate" class="font-bold text-[#001b3d]">出荷日</label>
        <input
          id="shipDate"
          type="date"
          v-model="selectedDate"
          class="h-14 w-[255px] rounded-[8px] border border-[#b9c7d8] bg-white px-5 text-[22px] outline-none focus:border-[#2563eb]"
          @change="loadDashboard"
        />
        <span class="whitespace-nowrap rounded-full bg-[#eef3ff] px-5 py-3 text-[21px] font-bold text-[#2457e6]">
          対象出荷日：{{ payload.ship_date || selectedDate }}
        </span>
      </div>
    </header>

    <section class="grid shrink-0 grid-cols-3 gap-[18px] py-[18px]">
      <SummaryCard title="集合梱包" :summary="payload.summary.pack" />
      <SummaryCard title="釣銭機系" :summary="payload.summary.cash" />
      <SummaryCard title="全体" :summary="payload.summary.overall" />
    </section>

    <section class="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[14px] border border-[#d3dce6] bg-white shadow-sm">
      <div class="flex min-h-[68px] shrink-0 items-center justify-between gap-6 border-b border-[#cbd6e2] px-5 py-3">
        <div class="text-[24px] font-bold">FFC出荷NO別 進捗詳細</div>
        <div class="flex shrink-0 flex-col items-end gap-1 text-right text-[#475569]">
          <div class="text-[18px] font-bold text-[#071d3a]">更新時刻：{{ lastUpdatedAt || "-" }}</div>
          <div class="text-[16px]">
            <span v-if="loading">読込中</span>
            <span v-else-if="error">{{ error }}</span>
            <span v-else-if="usingMock">デモデータ表示</span>
            <span v-else>※「集合梱包」「釣銭機系」「全体ステータス」の見出しクリックで 完了／未完 ソート</span>
          </div>
        </div>
      </div>

      <div class="min-h-0 flex-1 overflow-auto">
        <table class="w-full min-w-[1350px] table-fixed border-separate border-spacing-0 text-[22px]">
          <colgroup>
            <col class="w-[18%]" />
            <col class="w-[10%]" />
            <col class="w-[18%]" />
            <col class="w-[22%]" />
            <col class="w-[22%]" />
            <col class="w-[16%]" />
          </colgroup>
          <thead>
            <tr>
              <SortableTh label="FFC出荷NO" column="ffc_shipment_no" :sort-state="sortState" @sort="setSort" />
              <SortableTh label="店番" column="store_no" :sort-state="sortState" @sort="setSort" />
              <SortableTh label="店舗名" column="store_name" :sort-state="sortState" @sort="setSort" />
              <SortableTh label="集合梱包 シリアル取得" column="pack_complete" :sort-state="sortState" @sort="setSort" />
              <SortableTh label="釣銭機系 シリアル取得" column="cash_complete" :sort-state="sortState" @sort="setSort" />
              <SortableTh label="全体ステータス" column="overall_complete" :sort-state="sortState" @sort="setSort" />
            </tr>
          </thead>
          <tbody>
            <tr v-if="!hasRows">
              <td colspan="6" class="border-b border-[#d9e2ec] px-4 py-10 text-center text-slate-500">
                表示対象データがありません
              </td>
            </tr>
            <tr v-for="row in sortedRows" :key="row.ffc_shipment_no" class="odd:bg-white even:bg-[#f7f9fb]">
              <td class="h-[76px] border-b border-r border-[#d9e2ec] px-4 py-3 text-center font-medium">{{ row.ffc_shipment_no }}</td>
              <td class="h-[76px] border-b border-r border-[#d9e2ec] px-4 py-3 text-center">{{ row.store_no }}</td>
              <td class="h-[76px] border-b border-r border-[#d9e2ec] px-4 py-3 text-center">{{ row.store_name }}</td>
              <td :class="serialCellClass(row.pack_complete)">{{ row.pack }}</td>
              <td :class="serialCellClass(row.cash_complete)">{{ row.cash }}</td>
              <td class="h-[76px] border-b border-r border-[#d9e2ec] px-4 py-3 text-center">
                <span :class="statusClass(row.overall_complete)">
                  {{ row.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive } from "vue"
import SummaryCard from "./components/SummaryCard.vue"
import SortableTh from "./components/SortableTh.vue"
import { useAoiDashboard } from "./composables/useAoiDashboard"


const {
  selectedDate,
  payload,
  loading,
  error,
  usingMock,
  lastUpdatedAt,
  hasRows,
  loadDashboard,
} = useAoiDashboard()

const sortState = reactive({
  column: "ffc_shipment_no",
  direction: "asc",
})

const sortedRows = computed(() => {
  const direction = sortState.direction === "asc" ? 1 : -1
  return [...payload.value.rows].sort((a, b) => {
    const av = sortValue(a, sortState.column)
    const bv = sortValue(b, sortState.column)
    if (av < bv) return -1 * direction
    if (av > bv) return 1 * direction
    return String(a.ffc_shipment_no).localeCompare(String(b.ffc_shipment_no), "ja")
  })
})

function setSort(column) {
  if (sortState.column === column) {
    sortState.direction = sortState.direction === "asc" ? "desc" : "asc"
    return
  }
  sortState.column = column
  sortState.direction = "asc"
}

function sortValue(row, column) {
  if (["pack_complete", "cash_complete", "overall_complete"].includes(column)) {
    return row[column] ? 1 : 0
  }
  if (column === "store_no") {
    return Number(row[column]) || 0
  }
  return String(row[column] || "")
}

function serialCellClass(complete) {
  return [
    "h-[76px] border-b border-r border-[#d9e2ec] px-4 py-3 text-center text-[23px] font-bold",
    complete ? "bg-[#d8f8e2] text-[#006b35]" : "bg-white text-[#001b3d]",
  ]
}

function statusClass(complete) {
  return [
    "inline-flex min-w-[114px] items-center justify-center rounded-full px-5 py-2 text-[21px] font-bold",
    complete ? "bg-[#d8f8e2] text-[#006b35]" : "bg-[#fee2e2] text-[#991b1b]",
  ]
}
</script>
