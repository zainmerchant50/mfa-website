import React from 'react';
import {Composition} from 'remotion';
import {Listing, defaultProps} from './Listing.jsx';

// One template, two sizes. Duration comes from props.seconds (default 15 s: Etsy listing videos must be 5-15 s).
const FPS = 30;
const calc = ({props}) => ({durationInFrames: Math.round((props.seconds || 15) * FPS)});

export const Root = () => (
  <>
    <Composition
      id="Listing16x9"
      component={Listing}
      width={1920}
      height={1080}
      fps={FPS}
      durationInFrames={15 * FPS}
      defaultProps={defaultProps}
      calculateMetadata={calc}
    />
    <Composition
      id="Listing9x16"
      component={Listing}
      width={1080}
      height={1920}
      fps={FPS}
      durationInFrames={15 * FPS}
      defaultProps={defaultProps}
      calculateMetadata={calc}
    />
  </>
);
