// 把所有 .vue 里数值型 label-width="Npx" 统一 +50(表达式型如 formConf.labelWidth 不动)。
const fs = require('fs')
const path = require('path')
const delta = Number(process.argv[3] || 50)
let files = 0
let hits = 0

function walk(dir) {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name)
    const st = fs.statSync(p)
    if (st.isDirectory()) walk(p)
    else if (name.endsWith('.vue')) processFile(p)
  }
}
function processFile(f) {
  const src = fs.readFileSync(f, 'utf8')
  let n = 0
  const out = src.replace(/label-width="(\d+)px"/g, (m, w) => {
    n++
    return `label-width="${Number(w) + delta}px"`
  })
  if (n) {
    fs.writeFileSync(f, out, 'utf8')
    files++
    hits += n
    console.log(`  +${delta}px ×${n}  ${path.relative(process.cwd(), f)}`)
  }
}
walk(process.argv[2] || 'src')
console.log(`\n共 ${files} 文件 / ${hits} 处 label-width += ${delta}px`)
