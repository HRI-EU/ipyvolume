#extension GL_OES_standard_derivatives : enable
#define DEPTH_PACKING 3201
#define PHYSICAL

uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
uniform float emissiveIntensity;

#ifndef STANDARD
	uniform float clearCoat;
	uniform float clearCoatRoughness;
#endif

varying vec3 vViewPosition;

#ifndef FLAT_SHADED

	varying vec3 vNormal;

#endif

#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <uv2_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <bsdfs>
#include <cube_uv_reflection_fragment>
#include <envmap_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <lights_physical_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>

//////////////////////////////////////////////////////////////////
//#include <fog_pars_fragment>

varying vec4 vertex_color;
varying vec3 vertex_position;
varying vec2 vertex_uv;

#ifdef USE_TEXTURE
    uniform sampler2D texture;
    uniform sampler2D texture_previous;
    uniform float animation_time_texture;
#endif


void main(void) {
/*
  	vec4 finalColor2 = vec4( 0.0, 0.0, 0.0, 1.0 );
#ifdef USE_RGB
    finalColor2 = vertex_color;
#else
 #ifdef AS_LINE
    finalColor2 = vertex_color;
 #else
  #ifdef USE_SPRITE
   #ifdef USE_TEXTURE
    finalColor2 = mix(texture2D(texture_previous, vertex_uv), texture2D(texture, vertex_uv), animation_time_texture);
   #else
    finalColor2 = vertex_color;
   #endif
  #else
    vec3 fdx = dFdx( vertex_position );
    vec3 fdy = dFdy( vertex_position );
    vec3 normal = normalize( cross( fdx, fdy ) );
    float diffuse = dot( normal, vec3( 0.0, 0.0, 1.0 ) );

    finalColor2 = vec4(clamp(diffuse, 0.2, 1.) * vertex_color.rgb, vertex_color.a);
  #endif
 #endif
#endif
	#include <fog_fragment>
*/
//////////////////////////////////////////////////////

	#include <clipping_planes_fragment>

	vec4 diffuseColor = vec4( 1.0, 1.0, 1.0, opacity );
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive * emissiveIntensity;


	#include <logdepthbuf_fragment>
	#include <map_fragment>
	//#include <color_fragment>
//#ifdef USE_COLOR

//	diffuseColor.rgb *= vec3(1.0, 0.0, 0.0);

//#endif
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	/*
#ifdef FLAT_SHADED

	// Workaround for Adreno/Nexus5 not able able to do dFdx( vViewPosition ) ...

	vec3 fdx = vec3( dFdx( vViewPosition.x ), dFdx( vViewPosition.y ), dFdx( vViewPosition.z ) );
	vec3 fdy = vec3( dFdy( vViewPosition.x ), dFdy( vViewPosition.y ), dFdy( vViewPosition.z ) );
	vec3 normal = normalize( cross( fdx, fdy ) );

#else

	vec3 normal = normalize( vNormal );

	#ifdef DOUBLE_SIDED

		normal = normal * ( float( gl_FrontFacing ) * 2.0 - 1.0 );

	#endif

#endif
*/
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>

	// accumulation
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>

	// modulation
	#include <aomap_fragment>

	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;

	gl_FragColor = vec4( outgoingLight, diffuseColor.a );

	#include <tonemapping_fragment>
	#include <encodings_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>

#ifdef FLAT_SHADED
	gl_FragColor = vec4( 0.0,1.0,0.0, diffuseColor.a );

#endif

}