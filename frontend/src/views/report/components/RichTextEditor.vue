<template>
  <div class="rich-editor">
    <div class="editor-toolbar">
      <a-space size="mini" wrap>
        <a-button size="mini" type="outline" @click="execCommand('bold')" title="加粗">
          <strong>B</strong>
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('italic')" title="斜体">
          <em>I</em>
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('underline')" title="下划线">
          <u>U</u>
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('strikeThrough')" title="删除线">
          <s>S</s>
        </a-button>
        <a-divider type="vertical" style="margin: 0 4px;" />
        <a-select v-model="fontSize" size="mini" style="width: 90px;" placeholder="字号" @change="handleFontSize">
          <a-option value="1">12px</a-option>
          <a-option value="2">14px</a-option>
          <a-option value="3">16px</a-option>
          <a-option value="4">18px</a-option>
          <a-option value="5">24px</a-option>
          <a-option value="6">32px</a-option>
          <a-option value="7">48px</a-option>
        </a-select>
        <a-divider type="vertical" style="margin: 0 4px;" />
        <a-button size="mini" type="outline" @click="execCommand('foreColor', '#165DFF')" title="蓝色字">
          <span style="color: #165DFF;">A</span>
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('foreColor', '#00B42A')" title="绿色字">
          <span style="color: #00B42A;">A</span>
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('foreColor', '#F53F3F')" title="红色字">
          <span style="color: #F53F3F;">A</span>
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('foreColor', '#FF7D00')" title="橙色字">
          <span style="color: #FF7D00;">A</span>
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('foreColor', '#1d2129')" title="黑色字">
          <span style="color: #1d2129;">A</span>
        </a-button>
        <a-divider type="vertical" style="margin: 0 4px;" />
        <a-button size="mini" type="outline" @click="execCommand('hiliteColor', '#FFF3C4')" title="高亮">
          <icon-highlight />
        </a-button>
        <a-divider type="vertical" style="margin: 0 4px;" />
        <a-button size="mini" type="outline" @click="execCommand('justifyLeft')" title="左对齐">
          <icon-align-left />
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('justifyCenter')" title="居中对齐">
          <icon-align-center />
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('justifyRight')" title="右对齐">
          <icon-align-right />
        </a-button>
        <a-divider type="vertical" style="margin: 0 4px;" />
        <a-button size="mini" type="outline" @click="execCommand('insertUnorderedList')" title="无序列表">
          <icon-list />
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('insertOrderedList')" title="有序列表">
          <icon-ordered-list />
        </a-button>
        <a-divider type="vertical" style="margin: 0 4px;" />
        <a-button size="mini" type="outline" @click="execCommand('formatBlock', 'h1')" title="标题1">
          H1
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('formatBlock', 'h2')" title="标题2">
          H2
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('formatBlock', 'h3')" title="标题3">
          H3
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('formatBlock', 'p')" title="正文">
          P
        </a-button>
        <a-divider type="vertical" style="margin: 0 4px;" />
        <a-button size="mini" type="outline" @click="insertTable" title="插入表格">
          <icon-table />
        </a-button>
        <a-divider type="vertical" style="margin: 0 4px;" />
        <a-button size="mini" type="outline" @click="execCommand('undo')" title="撤销">
          <icon-undo />
        </a-button>
        <a-button size="mini" type="outline" @click="execCommand('redo')" title="重做">
          <icon-redo />
        </a-button>
        <a-divider type="vertical" style="margin: 0 4px;" />
        <a-button size="mini" type="outline" @click="toggleSource" title="源码模式">
          <icon-code />
        </a-button>
        <a-button size="mini" type="outline" @click="clearFormat" title="清除格式">
          <icon-delete />
        </a-button>
      </a-space>
    </div>
    <div class="editor-content-wrapper">
      <div
        v-if="!showSource"
        ref="editorRef"
        class="editor-content"
        contenteditable="true"
        @input="handleInput"
        @paste="handlePaste"
      ></div>
      <a-textarea
        v-else
        v-model="sourceCode"
        class="editor-source"
        :auto-size="{ minRows: 15, maxRows: 30 }"
        @input="handleSourceInput"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, nextTick } from 'vue'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const editorRef = ref<HTMLDivElement>()
const showSource = ref(false)
const sourceCode = ref('')
const fontSize = ref('')
const isInternalChange = ref(false)

const execCommand = (command: string, value?: string) => {
  editorRef.value?.focus()
  document.execCommand(command, false, value)
  handleInput()
}

const handleFontSize = (val: string) => {
  if (val) {
    execCommand('fontSize', val)
  }
}

const handleInput = () => {
  if (isInternalChange.value) {
    isInternalChange.value = false
    return
  }
  const html = editorRef.value?.innerHTML || ''
  emit('update:modelValue', html)
  sourceCode.value = html
}

const handlePaste = (e: ClipboardEvent) => {
  e.preventDefault()
  const text = e.clipboardData?.getData('text/html') || e.clipboardData?.getData('text/plain') || ''
  document.execCommand('insertHTML', false, text)
}

const insertTable = () => {
  const html = `<table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><th>列1</th><th>列2</th><th>列3</th></tr>
<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
</table><p><br></p>`
  execCommand('insertHTML', html)
}

const clearFormat = () => {
  execCommand('removeFormat')
}

const toggleSource = () => {
  showSource.value = !showSource.value
  if (!showSource.value && editorRef.value) {
    editorRef.value.innerHTML = sourceCode.value
  }
}

const handleSourceInput = () => {
  emit('update:modelValue', sourceCode.value)
  if (editorRef.value) {
    isInternalChange.value = true
    editorRef.value.innerHTML = sourceCode.value
  }
}

watch(() => props.modelValue, (val) => {
  if (editorRef.value && editorRef.value.innerHTML !== val) {
    isInternalChange.value = true
    editorRef.value.innerHTML = val || ''
  }
  sourceCode.value = val || ''
}, { immediate: true })

onMounted(() => {
  nextTick(() => {
    if (editorRef.value && props.modelValue) {
      editorRef.value.innerHTML = props.modelValue
    }
  })
})
</script>

<style scoped>
.rich-editor {
  border: 1px solid #e5e6eb;
  border-radius: 4px;
  overflow: hidden;
}

.editor-toolbar {
  padding: 10px 12px;
  background: #f7f8fa;
  border-bottom: 1px solid #e5e6eb;
}

.editor-toolbar :deep(.arco-btn) {
  min-width: 28px;
  padding: 0 6px;
}

.editor-content-wrapper {
  background: #fff;
}

.editor-content {
  min-height: 450px;
  padding: 16px 20px;
  outline: none;
  line-height: 1.8;
  font-size: 14px;
  color: #1d2129;
}

.editor-content:focus {
  outline: none;
}

.editor-content :deep(h1) {
  font-size: 24px;
  font-weight: 600;
  margin: 16px 0 12px 0;
}

.editor-content :deep(h2) {
  font-size: 20px;
  font-weight: 600;
  margin: 14px 0 10px 0;
}

.editor-content :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  margin: 12px 0 8px 0;
}

.editor-content :deep(p) {
  margin: 8px 0;
}

.editor-content :deep(ul),
.editor-content :deep(ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.editor-content :deep(li) {
  margin: 4px 0;
}

.editor-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.editor-content :deep(table th),
.editor-content :deep(table td) {
  border: 1px solid #e5e6eb;
  padding: 8px 12px;
}

.editor-content :deep(table th) {
  background: #f2f3f5;
  font-weight: 600;
}

.editor-content :deep(strong) {
  font-weight: 600;
}

.editor-source {
  border: none;
  border-radius: 0;
}

.editor-source :deep(.arco-textarea) {
  border: none;
  border-radius: 0;
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
}
</style>
