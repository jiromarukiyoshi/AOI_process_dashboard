export const mockDates = ["2026-06-18", "2026-06-19", "2026-06-20"]

const rows = {
  "2026-06-18": [
    ["F000200001", "11", "大仁店", 4, 4, 4, 4],
    ["F000200002", "22", "三島店", 3, 3, 3, 3],
    ["F000200003", "35", "沼津店", 2, 5, 1, 5],
    ["F000200004", "48", "富士店", 6, 6, 2, 6],
    ["F000200005", "52", "静岡店", 5, 5, 5, 5],
    ["F000200006", "67", "清水店", 1, 4, 4, 4],
    ["F000200007", "74", "藤枝店", 0, 3, 0, 3],
    ["F000200008", "86", "焼津店", 7, 7, 7, 7],
    ["F000200009", "91", "島田店", 3, 4, 4, 4],
    ["F000200010", "105", "掛川店", 2, 2, 2, 2],
  ],
  "2026-06-19": [
    ["F000200011", "118", "浜松店", 5, 5, 5, 5],
    ["F000200012", "121", "磐田店", 4, 4, 1, 4],
    ["F000200013", "134", "袋井店", 0, 3, 0, 3],
    ["F000200014", "146", "菊川店", 2, 2, 2, 2],
    ["F000200015", "152", "御前崎店", 2, 6, 6, 6],
    ["F000200016", "163", "牧之原店", 3, 3, 3, 3],
    ["F000200017", "177", "伊東店", 1, 5, 2, 5],
    ["F000200018", "188", "熱海店", 4, 4, 4, 4],
  ],
  "2026-06-20": [
    ["F000200021", "211", "長泉店", 6, 6, 6, 6],
    ["F000200022", "222", "裾野店", 5, 5, 5, 5],
    ["F000200023", "233", "御殿場店", 4, 7, 3, 7],
    ["F000200024", "244", "小山店", 0, 4, 0, 4],
    ["F000200025", "255", "函南店", 4, 4, 1, 4],
    ["F000200026", "266", "韮山店", 3, 3, 3, 3],
  ],
}

export function buildMockPayload(shipDate = mockDates[0]) {
  const tableRows = (rows[shipDate] || []).map(
    ([ffcShipmentNo, storeNo, storeName, packDone, packTotal, cashDone, cashTotal]) => {
      const packComplete = packDone === packTotal
      const cashComplete = cashDone === cashTotal
      const overallComplete = packComplete && cashComplete
      return {
        ffc_shipment_no: ffcShipmentNo,
        store_no: storeNo,
        store_name: storeName,
        pack: `${packDone}/${packTotal}`,
        cash: `${cashDone}/${cashTotal}`,
        status: overallComplete ? "完了" : "未完",
        pack_done: packDone,
        pack_total: packTotal,
        cash_done: cashDone,
        cash_total: cashTotal,
        pack_complete: packComplete,
        cash_complete: cashComplete,
        overall_complete: overallComplete,
      }
    },
  )

  const total = tableRows.length
  const packDone = tableRows.filter((row) => row.pack_complete).length
  const cashDone = tableRows.filter((row) => row.cash_complete).length
  const overallDone = tableRows.filter((row) => row.overall_complete).length

  return {
    ship_date: shipDate,
    summary: {
      pack: buildSummary(packDone, total),
      cash: buildSummary(cashDone, total),
      overall: buildSummary(overallDone, total),
    },
    rows: tableRows,
  }
}

function buildSummary(done, total) {
  return { done, total, rate: total ? Math.round((done / total) * 100) : 0 }
}
