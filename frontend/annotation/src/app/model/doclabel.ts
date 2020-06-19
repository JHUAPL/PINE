// (C) 2019 The Johns Hopkins University Applied Physics Laboratory LLC.

export class DocLabel {

    private static nextColorFirst = -20;
    private static nextColorSecond = 160;
    private static nextColorFirstDelta = 20;

    public name: string;
    public color: string;

    constructor(label: string) {
        this.name = label;
        this.color = DocLabel.getNextColor();
    }

    public equals(other: DocLabel): boolean {
        return this.name === other.name && this.color === other.color;
    }

    public static getLabels(labels: string[]): DocLabel[] {
        const parsedLabels: DocLabel[] = [];
        labels.sort();
        DocLabel.resetColors();
        labels.forEach(element => {
            parsedLabels.push(new DocLabel(element));
        });
        return parsedLabels;
    }

    private static getNextColor(): string {
        DocLabel.nextColorFirst = DocLabel.nextColorFirst + DocLabel.nextColorFirstDelta;

        if(DocLabel.nextColorFirst % 360 === 0) {
            DocLabel.nextColorFirstDelta = DocLabel.nextColorFirstDelta + 10;
            DocLabel.nextColorSecond = DocLabel.nextColorSecond - 40;
        }

        if(DocLabel.nextColorSecond === 0) {
            DocLabel.nextColorSecond = 160;
        }

        return "hsl(" + DocLabel.nextColorFirst + "," + DocLabel.nextColorSecond + "%,75%)";
    }

    public static resetColors() {
        DocLabel.nextColorFirst = -20;
        DocLabel.nextColorSecond = 160;
    }
}
