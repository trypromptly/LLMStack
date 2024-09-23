export const columnIndexToLetter = (index) => {
  let temp = index + 1;
  let letter = "";
  while (temp > 0) {
    let remainder = (temp - 1) % 26;
    letter = String.fromCharCode(65 + remainder) + letter;
    temp = Math.floor((temp - 1) / 26);
  }
  return letter;
};

export const columnLetterToIndex = (letter) => {
  if (!letter) return 0;

  return (
    letter.split("").reduce((acc, char, index) => {
      return (
        acc +
        (char.charCodeAt(0) - 64) * Math.pow(26, letter.length - index - 1)
      );
    }, 0) - 1
  );
};

export const cellIdToGridCell = (cellId, columns) => {
  const match = cellId.match(/([A-Z]+)(\d+)/);
  if (!match) return null;
  const [, colLetter, rowString] = match;
  const row = parseInt(rowString, 10) - 1;
  const col = columns.findIndex((c) => c.col_letter === colLetter);
  return [col, row];
};

export const gridCellToCellId = (gridCell, columns) => {
  const [colIndex, rowIndex] = gridCell;
  const colLetter = columns[colIndex].col_letter;
  return `${colLetter}${rowIndex + 1}`;
};
