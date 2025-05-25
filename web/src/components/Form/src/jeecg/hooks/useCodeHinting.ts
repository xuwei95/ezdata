export const useCodeHinting = (CodeMirror, keywords, language) => {
  const currentKeywords: any = [...keywords];
  const codeHintingMount = (coder) => {
    if (keywords.length) {
      coder.setOption('mode', language);
      setTimeout(() => {
        coder!.on('cursorActivity', function () {
          coder?.showHint({
            completeSingle: false,
            // container: containerRef.value
          });
        });
      }, 1e3);
    }
  };
  const codeHintingRegistry = () => {
    const funcsHint = (cm, callback) => {
      // 获取光标位置
      const cur = cm.getCursor();
      // 获取当前单词的信息
      const token = cm.getTokenAt(cur);
      const start = token.start;
      const end = cur.ch;
      const str = token.string;

      if (str.length) {
        const findIdx = (a, b) => a.toLowerCase().indexOf(b.toLowerCase());
        let list = currentKeywords
          .filter((item) => {
            const index = findIdx(item, str);
            return (index === 0 || index === 1) && (item.length != str.length || item.length - 1 != str.length);
          })
          .sort((a, b) => {
            if (findIdx(a, str) < findIdx(b, str)) {
              return -1;
            } else {
              return 1;
            }
          });

        // 有点去掉点
        // list = list.map(item => {
        //   if(item.indexOf(".") === 0){
        //     return item.substring(1);
        //   }
        //   return item;
        // });
        if (list.length === 1 && (list[0] === str || list[0].substring(1) === str)) {
          list = [];
        }
        if (list.length) {
          callback({
            list: list,
            from: CodeMirror.Pos(cur.line, start),
            to: CodeMirror.Pos(cur.line, end),
          });
        }
      }
    };
    funcsHint.async = true;
    funcsHint.supportsSelection = true;
    // 自动补全
    keywords.length && CodeMirror.registerHelper('hint', language, funcsHint);
  };
  return {
    codeHintingRegistry,
    codeHintingMount,
  };
};
