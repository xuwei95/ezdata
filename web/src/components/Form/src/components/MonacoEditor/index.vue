<template>
  <div ref="codeEditBox" class="codeEditBox" :class="hightChange && 'codeEditBox1'" :style="{ height: height }"></div>
</template>
<script lang="ts">
  import { defineComponent, onBeforeUnmount, onMounted, ref, watch } from 'vue';
  import JsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker';
  import CssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker';
  import HtmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker';
  import TsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker';
  import EditorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker';
  import * as monaco from 'monaco-editor';
  import { language as pyLanguage } from 'monaco-editor/esm/vs/basic-languages/python/python.js';
  import { language as sqlLanguage } from 'monaco-editor/esm/vs/basic-languages/sql/sql.js';
  import { language as yamlLanguage } from 'monaco-editor/esm/vs/basic-languages/yaml/yaml.js';
  import 'monaco-editor/esm/vs/basic-languages/sql/sql.contribution';
  import { editorProps } from './monacoEditorType';
  export default defineComponent({
    name: 'MonacoEditor',
    props: editorProps,
    emits: ['change', 'update:value', 'editor-mounted'],
    setup(props, { emit }) {
      (self as any).MonacoEnvironment = {
        getWorker(_: string, label: string) {
          if (label === 'json') {
            return new JsonWorker();
          }
          if (['css', 'scss', 'less'].includes(label)) {
            return new CssWorker();
          }
          if (['html', 'handlebars', 'razor'].includes(label)) {
            return new HtmlWorker();
          }
          if (['typescript', 'javascript'].includes(label)) {
            return new TsWorker();
          }
          return new EditorWorker();
        },
      };
      let editor: any;
      const codeEditBox = ref();

      const initialize = () => {
        console.log('init66666', props);
        monaco.languages.typescript.javascriptDefaults.setDiagnosticsOptions({
          noSemanticValidation: true,
          noSyntaxValidation: false,
        });
        monaco.languages.typescript.javascriptDefaults.setCompilerOptions({
          target: monaco.languages.typescript.ScriptTarget.ES2020,
          allowNonTsExtensions: true,
        });
        monaco.languages.registerCompletionItemProvider('sql', {
          provideCompletionItems() {
            const suggestions: any = [];
            // 这个keywords就是sql.js文件中有的
            sqlLanguage.keywords.forEach((item: any) => {
              suggestions.push({
                label: item,
                kind: monaco.languages.CompletionItemKind.Keyword,
                insertText: item,
              });
            });
            sqlLanguage.operators.forEach((item: any) => {
              suggestions.push({
                label: item,
                kind: monaco.languages.CompletionItemKind.Operator,
                insertText: item,
              });
            });
            sqlLanguage.builtinFunctions.forEach((item: any) => {
              suggestions.push({
                label: item,
                kind: monaco.languages.CompletionItemKind.Function,
                insertText: item,
              });
            });
            sqlLanguage.builtinVariables.forEach((item: any) => {
              suggestions.push({
                label: item,
                kind: monaco.languages.CompletionItemKind.Variable,
                insertText: item,
              });
            });
            return {
              // 最后要返回一个数组
              suggestions,
            };
          },
        });
        monaco.languages.registerCompletionItemProvider('python', {
          provideCompletionItems() {
            const suggestions: any = [];
            // 这个keywords就是python.js文件中有的
            pyLanguage.keywords.forEach((item: any) => {
              suggestions.push({
                label: item,
                kind: monaco.languages.CompletionItemKind.Keyword,
                insertText: item,
              });
            });
            return {
              // 最后要返回一个数组
              suggestions,
            };
          },
        });
        monaco.languages.registerCompletionItemProvider('yaml', {
          provideCompletionItems() {
            const suggestions: any = [];
            // 这个keywords就是python.js文件中有的
            yamlLanguage.keywords.forEach((item: any) => {
              suggestions.push({
                label: item,
                kind: monaco.languages.CompletionItemKind.Keyword,
                insertText: item,
              });
            });
            return {
              // 最后要返回一个数组
              suggestions,
            };
          },
        });
        editor = monaco.editor.create(codeEditBox.value, {
          value: props.value,
          language: props.language,
          readOnly: props.disabled,
          theme: props.theme,
          ...props.options,
        });

        // 监听值的变化
        editor.onDidChangeModelContent(() => {
          const value = editor.getValue(); // 给父组件实时返回最新文本
          emit('update:value', value);
          emit('change', value);
        });

        emit('editor-mounted', editor);
      };
      watch(
        () => props.value,
        (newValue) => {
          console.log('change66666', props);
          if (editor) {
            const value = editor.getValue();
            if (newValue !== value) {
              editor.setValue(newValue);
            }
          }
        }
      );

      watch(
        () => props.options,
        (newValue) => {
          editor.updateOptions(newValue);
        },
        { deep: true }
      );
      watch(
        () => props.disabled,
        () => {
          console.log('props.disabled', props.disabled);
          editor.updateOptions({ readOnly: props.disabled });
        },
        { deep: true }
      );

      watch(
        () => props.language,
        (newValue) => {
          monaco.editor.setModelLanguage(editor.getModel()!, newValue);
        }
      );

      onBeforeUnmount(() => {
        editor.dispose();
      });

      onMounted(() => {
        console.log('mou', props);
        initialize();
      });

      return { codeEditBox };
    },
  });
</script>

<style lang="scss" scoped>
  .codeEditBox {
    width: 100%;
    flex: 1;
    min-height: 200px;
    overflow-y: auto;
  }
  .codeEditBox1 {
    height: calc(100% - 323px);
  }
</style>
