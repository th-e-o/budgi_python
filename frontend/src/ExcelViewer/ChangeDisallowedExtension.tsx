import { Shape, type UniverRenderingContext, type IShapeProps } from '@univerjs/presets/preset-sheets-core';
import type {IViewportInfo} from "@univerjs/engine-render";

interface IFlashProps extends IShapeProps {
    initialColor: [number, number, number];
    duration: number;
}

export class AnimatedFlashObject extends Shape<IFlashProps> {
    private readonly startTime: number;

    private readonly initialColor: [number, number, number];
    private readonly duration: number;

    constructor(key: string, props: IFlashProps) {
        // left, top, width, height, zIndex
        super(key, props);

        this.startTime = Date.now();
        this.initialColor = props.initialColor;
        this.duration = props.duration;
    }

    /**
     * This override is now fully correct.
     */
    protected override _draw(ctx: UniverRenderingContext, bounds?: IViewportInfo) {
        const { width, height, initialColor, duration } = this;

        if (!width || !height) return;

        const elapsedTime = Date.now() - this.startTime;

        if (elapsedTime >= duration) {
            this.parent?.removeObject(this);
            return;
        }

        const currentAlpha = 0.4 * Math.max(0, 1 - (elapsedTime / duration));

        ctx.fillStyle = `rgba(${initialColor.join(',')}, ${currentAlpha})`;

        ctx.fillRect(0, 0, width, height);
    }
}