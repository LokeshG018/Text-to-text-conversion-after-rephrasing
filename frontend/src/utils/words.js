const STOP = new Set('the a an and or but of to in on for with is are was were be been it its this that these those as at by from they their them we our you your i he she his her not no can will would should could has have had do does did into than then so such more most'.split(' '))

export function wordFrequencies(texts, limit = 40) {
  const counts = {}
  texts.join(' ').toLowerCase().match(/[a-z']{3,}/g)?.forEach((w) => { if (!STOP.has(w)) counts[w] = (counts[w] || 0) + 1 })
  return Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, limit)
}
