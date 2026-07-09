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

    <nav class="flex shrink-0 items-center gap-3 pt-[18px]" aria-label="表示切替">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        type="button"
        :class="tabButtonClass(tab.key)"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </nav>

    <section v-if="activeTab === 'progress'" class="grid shrink-0 grid-cols-3 gap-[18px] py-[18px]">
      <SummaryCard title="集合梱包" :summary="payload.summary.pack" />
      <SummaryCard title="釣銭機系" :summary="payload.summary.cash" />
      <SummaryCard title="全体" :summary="payload.summary.overall" />
    </section>

    <section v-if="activeTab === 'progress'" class="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[14px] border border-[#d3dce6] bg-white shadow-sm">
      <div class="flex min-h-[68px] shrink-0 items-center justify-between gap-6 border-b border-[#cbd6e2] px-5 py-3">
        <div class="text-[24px] font-bold">FFC出荷NO別 進捗詳細</div>
        <StatusInfo :loading="loading" :error="error" :using-mock="usingMock" :last-updated-at="lastUpdatedAt" />
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
              <SortableTh label="FFC出荷NO" column="ffc_shipment_no" :sort-state="progressSort" @sort="setProgressSort" />
              <SortableTh label="店番" column="store_no" :sort-state="progressSort" @sort="setProgressSort" />
              <SortableTh label="店舗名" column="store_name" :sort-state="progressSort" @sort="setProgressSort" />
              <SortableTh label="集合梱包 シリアル取得" column="pack_complete" :sort-state="progressSort" @sort="setProgressSort" />
              <SortableTh label="釣銭機系 シリアル取得" column="cash_complete" :sort-state="progressSort" @sort="setProgressSort" />
              <SortableTh label="全体ステータス" column="overall_complete" :sort-state="progressSort" @sort="setProgressSort" />
            </tr>
          </thead>
          <tbody>
            <tr v-if="!hasRows">
              <td colspan="6" class="border-b border-[#d9e2ec] px-4 py-10 text-center text-slate-500">
                表示対象データがありません
              </td>
            </tr>
            <tr v-for="row in sortedProgressRows" :key="row.ffc_shipment_no" class="odd:bg-white even:bg-[#f7f9fb]">
              <td class="table-cell-main font-medium">{{ row.ffc_shipment_no }}</td>
              <td class="table-cell-main">{{ row.store_no }}</td>
              <td class="table-cell-main">{{ row.store_name }}</td>
              <td :class="serialCellClass(row.pack_complete)">{{ row.pack }}</td>
              <td :class="serialCellClass(row.cash_complete)">{{ row.cash }}</td>
              <td class="table-cell-main">
                <span :class="statusClass(row.overall_complete)">{{ row.status }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-else class="mt-[18px] flex min-h-0 flex-1 flex-col overflow-hidden rounded-[14px] border border-[#d3dce6] bg-white shadow-sm">
      <div class="flex min-h-[68px] shrink-0 items-center justify-between gap-6 border-b border-[#cbd6e2] px-5 py-3">
        <div class="text-[24px] font-bold">店舗単位 シリアル一覧</div>
        <StatusInfo :loading="loading" :error="error" :using-mock="usingMock" :last-updated-at="lastUpdatedAt" />
      </div>

      <div class="grid shrink-0 grid-cols-8 gap-3 border-b border-[#d9e2ec] bg-[#f8fafc] px-4 py-4 text-[16px]">
        <label v-for="filter in serialFilters" :key="filter.key" class="flex min-w-0 flex-col gap-1 font-bold text-[#29405f]">
          <span>{{ filter.label }}</span>
          <select
            v-if="filter.type === 'select'"
            v-model="serialFilterState[filter.key]"
            class="h-11 rounded-[8px] border border-[#b9c7d8] bg-white px-3 text-[18px] font-medium outline-none focus:border-[#2563eb]"
          >
            <option v-for="option in filter.options" :key="option" :value="option">{{ option }}</option>
          </select>
          <input
            v-else
            v-model.trim="serialFilterState[filter.key]"
            type="text"
            class="h-11 rounded-[8px] border border-[#b9c7d8] bg-white px-3 text-[18px] font-medium outline-none focus:border-[#2563eb]"
          />
        </label>
      </div>

      <div class="flex min-h-0 flex-1 overflow-auto">
        <table class="w-full min-w-[1900px] table-fixed border-separate border-spacing-0 text-[20px]">
          <colgroup>
            <col class="w-[10%]" />
            <col class="w-[13%]" />
            <col class="w-[7%]" />
            <col class="w-[8%]" />
            <col class="w-[14%]" />
            <col class="w-[10%]" />
            <col class="w-[12%]" />
            <col class="w-[19%]" />
            <col class="w-[7%]" />
          </colgroup>
          <thead>
            <tr>
              <SortableTh label="出荷日" column="ship_date" :sort-state="serialSort" @sort="setSerialSort" />
              <SortableTh label="FFC出荷NO" column="ffc_shipment_no" :sort-state="serialSort" @sort="setSerialSort" />
              <SortableTh label="枝番" column="eda_no" :sort-state="serialSort" @sort="setSerialSort" />
              <SortableTh label="店番" column="store_no" :sort-state="serialSort" @sort="setSerialSort" />
              <SortableTh label="店舗名" column="store_name" :sort-state="serialSort" @sort="setSerialSort" />
              <SortableTh label="区分" column="category" :sort-state="serialSort" @sort="setSerialSort" />
              <SortableTh label="製品コード" column="item_code" :sort-state="serialSort" @sort="setSerialSort" />
              <SortableTh label="製品名" column="item_name" :sort-state="serialSort" @sort="setSerialSort" />
              <SortableTh label="ステータス" column="status" :sort-state="serialSort" @sort="setSerialSort" />
            </tr>
          </thead>
          <tbody>
            <tr v-if="!filteredSerialRows.length">
              <td colspan="9" class="border-b border-[#d9e2ec] px-4 py-10 text-center text-slate-500">
                表示対象データがありません
              </td>
            </tr>
            <tr v-for="row in sortedSerialRows" :key="serialRowKey(row)" class="odd:bg-white even:bg-[#f7f9fb]">
              <td class="serial-cell">{{ row.ship_date }}</td>
              <td class="serial-cell font-medium">{{ row.ffc_shipment_no }}</td>
              <td class="serial-cell">{{ row.eda_no }}</td>
              <td class="serial-cell">{{ row.store_no }}</td>
              <td class="serial-cell">{{ row.store_name }}</td>
              <td class="serial-cell">{{ row.category }}</td>
              <td class="serial-cell">{{ row.item_code }}</td>
              <td class="serial-cell text-left">{{ row.item_name }}</td>
              <td class="serial-cell">
                <span :class="statusClass(row.status === '完了')">{{ row.status }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue"
import SummaryCard from "./components/SummaryCard.vue"
import SortableTh from "./components/SortableTh.vue"
import { useAoiDashboard } from "./composables/useAoiDashboard"


const {
  selectedDate,
  payload,
  serialPayload,
  loading,
  error,
  usingMock,
  lastUpdatedAt,
  hasRows,
  loadDashboard,
} = useAoiDashboard()

const StatusInfo = {
  props: {
    loading: Boolean,
    error: String,
    usingMock: Boolean,
    lastUpdatedAt: String,
  },
  template: `<div class="flex shrink-0 flex-col items-end gap-1 text-right text-[#475569]">
    <div class="text-[18px] font-bold text-[#071d3a]">更新時刻：{{ lastUpdatedAt || "-" }}</div>
    <div class="text-[16px]">
      <span v-if="loading">読込中</span>
      <span v-else-if="error">{{ error }}</span>
      <span v-else-if="usingMock">デモデータ表示</span>
      <span v-else>見出しクリックで並び替え</span>
    </div>
  </div>`,
}

const tabs = [
  { key: "progress", label: "FFC出荷NO別 進捗一覧" },
  { key: "serials", label: "店舗単位 シリアル一覧" },
]

const activeTab = ref("progress")

const progressSort = reactive({
  column: "ffc_shipment_no",
  direction: "asc",
})

const serialSort = reactive({
  column: "ffc_shipment_no",
  direction: "asc",
})

const serialFilterState = reactive({
  ship_date: "",
  ffc_shipment_no: "",
  store_no: "",
  store_name: "",
  item_code: "",
  item_name: "",
  category: "すべて",
  status: "すべて",
})

const serialFilters = [
  { key: "ship_date", label: "出荷日", type: "text" },
  { key: "ffc_shipment_no", label: "FFC出荷NO", type: "text" },
  { key: "store_no", label: "店番", type: "text" },
  { key: "store_name", label: "店舗名", type: "text" },
  { key: "item_code", label: "製品コード", type: "text" },
  { key: "item_name", label: "製品名", type: "text" },
  { key: "category", label: "区分", type: "select", options: ["すべて", "集合梱包", "釣銭機系"] },
  { key: "status", label: "ステータス", type: "select", options: ["すべて", "完了", "未完"] },
]

const sortedProgressRows = computed(() => {
  const direction = progressSort.direction === "asc" ? 1 : -1
  return [...payload.value.rows].sort((a, b) => compareRows(a, b, progressSort.column, direction, "ffc_shipment_no"))
})

const filteredSerialRows = computed(() => {
  return serialPayload.value.rows.filter((row) => {
    return serialFilters.every((filter) => {
      const selected = serialFilterState[filter.key]
      if (!selected || selected === "すべて") return true
      if (filter.type === "select") return row[filter.key] === selected
      return String(row[filter.key] || "").toLowerCase().includes(String(selected).toLowerCase())
    })
  })
})

const sortedSerialRows = computed(() => {
  const direction = serialSort.direction === "asc" ? 1 : -1
  return [...filteredSerialRows.value].sort((a, b) => compareRows(a, b, serialSort.column, direction, "ffc_shipment_no"))
})

function setProgressSort(column) {
  setSort(progressSort, column)
}

function setSerialSort(column) {
  setSort(serialSort, column)
}

function setSort(sortState, column) {
  if (sortState.column === column) {
    sortState.direction = sortState.direction === "asc" ? "desc" : "asc"
    return
  }
  sortState.column = column
  sortState.direction = "asc"
}

function compareRows(a, b, column, direction, fallbackColumn) {
  const av = sortValue(a, column)
  const bv = sortValue(b, column)
  if (av < bv) return -1 * direction
  if (av > bv) return 1 * direction
  return String(a[fallbackColumn] || "").localeCompare(String(b[fallbackColumn] || ""), "ja")
}

function sortValue(row, column) {
  if (["pack_complete", "cash_complete", "overall_complete"].includes(column)) {
    return row[column] ? 1 : 0
  }
  if (["store_no", "eda_no"].includes(column)) {
    return Number(row[column]) || 0
  }
  if (column === "status") {
    return row[column] === "完了" ? 1 : 0
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
    "inline-flex min-w-[104px] items-center justify-center rounded-full px-5 py-2 text-[20px] font-bold",
    complete ? "bg-[#d8f8e2] text-[#006b35]" : "bg-[#fee2e2] text-[#991b1b]",
  ]
}

function tabButtonClass(tabKey) {
  return [
    "h-[52px] rounded-[8px] border px-6 py-3 text-[20px] font-bold transition",
    activeTab.value === tabKey
      ? "border-[#2563eb] bg-[#2563eb] text-white shadow-sm"
      : "border-[#cbd6e2] bg-white text-[#29405f] hover:border-[#2563eb]",
  ]
}

function serialRowKey(row) {
  return [row.ship_date, row.ffc_shipment_no, row.eda_no, row.item_code, row.status].join("|")
}
</script>

<style scoped>
.table-cell-main {
  height: 76px;
  border-right: 1px solid #d9e2ec;
  border-bottom: 1px solid #d9e2ec;
  padding: 12px 16px;
  text-align: center;
}

.serial-cell {
  height: 64px;
  border-right: 1px solid #d9e2ec;
  border-bottom: 1px solid #d9e2ec;
  padding: 10px 14px;
  text-align: center;
  vertical-align: middle;
}
</style>