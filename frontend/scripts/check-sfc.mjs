import { globSync, readFileSync } from 'node:fs'
import { parse, compileScript, compileTemplate, compileStyleAsync } from '@vue/compiler-sfc'

const files = globSync('src/**/*.vue').sort()
let failed = 0

const srcRoot = `${process.cwd().replaceAll('\\', '/')}/src`
const variables = readFileSync(`${srcRoot}/styles/variables.scss`, 'utf8')
const resolveAlias = (content) => content.replace(/@use\s+'@\/styles\/variables\.scss'\s+as\s+\*;/, variables)

for (const file of files) {
  const source = readFileSync(file, 'utf8')
  const id = file.replace(/[^a-zA-Z0-9]/g, '_')
  const problems = []

  try {
    const { descriptor, errors } = parse(source, { filename: file })
    if (errors.length) {
      problems.push(...errors.map((e) => `parse: ${e.message}`))
    }
    if (descriptor.script || descriptor.scriptSetup) {
      try {
        compileScript(descriptor, { id })
      } catch (error) {
        problems.push(`script: ${error.message}`)
      }
    }
    if (descriptor.template) {
      const result = compileTemplate({
        source: descriptor.template.content,
        filename: file,
        id,
      })
      problems.push(...result.errors.map((e) => `template: ${e.message || e}`))
    }
    for (const style of descriptor.styles) {
      const result = await compileStyleAsync({
        source: resolveAlias(style.content),
        filename: file,
        id,
        scoped: style.scoped,
        preprocessLang: style.lang,
      })
      problems.push(...result.errors.map((e) => `style: ${e.message || e}`))
    }
  } catch (error) {
    problems.push(`fatal: ${error.message}`)
  }

  if (problems.length) {
    failed += 1
    console.log(`[FAIL] ${file}`)
    for (const problem of problems) console.log(`       ${problem}`)
  } else {
    console.log(`[PASS] ${file}`)
  }
}

console.log(`\n共 ${files.length} 个组件，失败 ${failed} 个`)
if (failed > 0) process.exit(1)