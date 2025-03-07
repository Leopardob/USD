#!/pxrpythonsubst
#
# Copyright 2017 Pixar
#
# Licensed under the terms set forth in the LICENSE.txt file available at
# https://openusd.org/license.

import sys, os, unittest
from pxr import Gf, Usd, UsdGeom, Sdf, Tf, Vt

class TestUsdGeomPrimvarsAPI(unittest.TestCase):
    def test_PrimvarsAPI(self):
        IsPrimvar = UsdGeom.Primvar.IsPrimvar

        # We'll put all our Primvar on a single mesh gprim
        stage = Usd.Stage.CreateInMemory('myTest.usda')
        gp = UsdGeom.Mesh.Define(stage, '/myMesh')
        gp_pv = UsdGeom.PrimvarsAPI(gp)

        nPasses = 3

        # Add three Primvars
        u1 = gp_pv.CreatePrimvar('u_1', Sdf.ValueTypeNames.FloatArray)
        self.assertFalse( u1.NameContainsNamespaces() )
        self.assertEqual(UsdGeom.Primvar.StripPrimvarsName(u1.GetName()), "u_1")
        # Make sure it's OK to manually specify the classifier namespace
        v1 = gp_pv.CreatePrimvar('primvars:v_1', Sdf.ValueTypeNames.FloatArray)
        self.assertEqual(UsdGeom.Primvar.StripPrimvarsName(v1.GetName()), "v_1")
        noPrimvarsPrefixName = "noPrimvarPrefixName"
        self.assertEqual(UsdGeom.Primvar.StripPrimvarsName(noPrimvarsPrefixName), noPrimvarsPrefixName)
        self.assertFalse( v1.NameContainsNamespaces() )
        _3dpmats = gp_pv.CreatePrimvar('projMats', Sdf.ValueTypeNames.Matrix4dArray,
                                    "constant", nPasses)
        
        # ensure we can create a primvar that contains namespaces!
        primvarName = 'skel:jointWeights'
        jointWeights = gp_pv.CreatePrimvar(primvarName, Sdf.ValueTypeNames.FloatArray)
        self.assertTrue( IsPrimvar(jointWeights) )
        self.assertTrue(UsdGeom.Primvar.IsValidPrimvarName(jointWeights.GetName()))
        self.assertTrue( jointWeights.NameContainsNamespaces() )
        self.assertEqual(primvarName, jointWeights.GetPrimvarName())

        # Ensure we cannot create a primvar named indices or any namespace
        # ending in indices
        with self.assertRaises(Tf.ErrorException):
            gp_pv.CreatePrimvar("indices", Sdf.ValueTypeNames.IntArray)
        with self.assertRaises(Tf.ErrorException):
            gp_pv.CreatePrimvar("multi:aggregate:indices", Sdf.ValueTypeNames.IntArray)

        self.assertEqual(len( gp_pv.GetAuthoredPrimvars() ), 4)
        # displayColor and displayOpacity are builtins, not authored
        self.assertEqual(len( gp_pv.GetPrimvars() ), 6)
        
        # Now add some random properties, plus a "manually" created, namespaced
        # primvar, and reverify
        p = gp.GetPrim()
        p.CreateRelationship("myBinding")
        p.CreateAttribute("myColor", Sdf.ValueTypeNames.Color3f)
        p.CreateAttribute("primvars:some:overly:namespaced:Color",
                          Sdf.ValueTypeNames.Color3f)

        datas = gp_pv.GetAuthoredPrimvars()

        self.assertEqual(len(datas), 5)
        self.assertTrue( IsPrimvar(datas[0]) )
        self.assertTrue(UsdGeom.Primvar.IsValidPrimvarName(datas[0].GetName()))
        self.assertTrue(UsdGeom.PrimvarsAPI.CanContainPropertyName(datas[0].GetName()))
        self.assertTrue( IsPrimvar(datas[1]) )
        self.assertTrue(UsdGeom.Primvar.IsValidPrimvarName(datas[1].GetName()))
        self.assertTrue(UsdGeom.PrimvarsAPI.CanContainPropertyName(datas[1].GetName()))
        # For variety, test the explicit Attribute extractor
        self.assertTrue( IsPrimvar(datas[2].GetAttr()) )
        self.assertTrue(UsdGeom.Primvar.IsValidPrimvarName(datas[2].GetAttr().GetName()))
        self.assertTrue(UsdGeom.PrimvarsAPI.CanContainPropertyName(datas[2].GetAttr().GetName()))
        self.assertFalse( IsPrimvar(p.GetAttribute("myColor")) )
        self.assertFalse(UsdGeom.Primvar.IsValidPrimvarName("myColor"))
        self.assertFalse(UsdGeom.PrimvarsAPI.CanContainPropertyName("myColor"))
        # Here we're testing that the speculative constructor fails properly
        self.assertFalse( IsPrimvar(UsdGeom.Primvar(p.GetAttribute("myColor"))) )
        self.assertFalse(UsdGeom.Primvar.IsValidPrimvarName(datas[0].GetIndicesAttr().GetName()))
        self.assertTrue(UsdGeom.PrimvarsAPI.CanContainPropertyName(datas[0].GetIndicesAttr().GetName()))
        # And here that the speculative constructor succeeds properly
        self.assertTrue( IsPrimvar(UsdGeom.Primvar(p.GetAttribute(v1.GetName()))) )


        # Some of the same tests, exercising the bool-type operator
        # for UsdGeomPrimvar; Primvar provides the easiest way to get INvalid attrs!
        self.assertTrue( datas[0] )
        self.assertTrue( datas[1] )
        self.assertTrue( datas[2] )
        self.assertFalse( UsdGeom.Primvar(p.GetAttribute("myColor")) )
        self.assertFalse( UsdGeom.Primvar(p.GetAttribute("myBinding")) )
        self.assertTrue( UsdGeom.Primvar(p.GetAttribute(v1.GetName())) )
        
        # Same classification test through GprimSchema API
        self.assertTrue( gp_pv.HasPrimvar('u_1') )
        self.assertTrue( gp_pv.HasPrimvar('v_1') )
        self.assertTrue( gp_pv.HasPrimvar('projMats') )
        self.assertTrue( gp_pv.HasPrimvar('skel:jointWeights') )
        self.assertFalse( gp_pv.HasPrimvar('myColor') )
        self.assertFalse( gp_pv.HasPrimvar('myBinding') )

        # Test that the gpv's returned by GetPrimvars are REALLY valid,
        # and that the UsdAttribute metadata wrappers work
        self.assertEqual( datas[0].GetTypeName(), Sdf.ValueTypeNames.Matrix4dArray )
        self.assertEqual( datas[3].GetTypeName(), Sdf.ValueTypeNames.FloatArray )
        self.assertEqual( datas[4].GetBaseName(), "v_1" )
        
        # Now we'll add some extra configuration and verify that the 
        # interrogative API works properly
        self.assertEqual( u1.GetInterpolation(), UsdGeom.Tokens.constant )  # fallback
        self.assertFalse( u1.HasAuthoredInterpolation() )
        self.assertFalse( u1.HasAuthoredElementSize() )
        self.assertTrue( u1.SetInterpolation(UsdGeom.Tokens.vertex) )
        self.assertTrue( u1.HasAuthoredInterpolation() )
        self.assertEqual( u1.GetInterpolation(), UsdGeom.Tokens.vertex )

        self.assertFalse( v1.HasAuthoredInterpolation() )
        self.assertFalse( v1.HasAuthoredElementSize() )
        self.assertTrue( v1.SetInterpolation(UsdGeom.Tokens.uniform) )
        self.assertTrue( v1.SetInterpolation(UsdGeom.Tokens.varying) )
        self.assertTrue( v1.SetInterpolation(UsdGeom.Tokens.constant) )
        self.assertTrue( v1.SetInterpolation(UsdGeom.Tokens.faceVarying) )

        with self.assertRaises(Tf.ErrorException):
            v1.SetInterpolation("frobosity")
        # Should be the last good value set
        self.assertEqual( v1.GetInterpolation(), "faceVarying" )

        self.assertTrue( _3dpmats.HasAuthoredInterpolation() )
        self.assertTrue( _3dpmats.HasAuthoredElementSize() )
        with self.assertRaises(Tf.ErrorException):
            _3dpmats.SetElementSize(0)
        # Failure to set shouldn't change the state...
        self.assertTrue( _3dpmats.HasAuthoredElementSize() )
        self.assertTrue( _3dpmats.SetElementSize(nPasses) )
        self.assertTrue( _3dpmats.HasAuthoredElementSize() )

        # Make sure value Get/Set work
        self.assertEqual( u1.Get(), None )

        self.assertFalse(u1.IsIndexed())
        self.assertFalse(u1.GetIndicesAttr())
        self.assertEqual(u1.ComputeFlattened(), None)

        uVal = Vt.FloatArray([1.1,2.1,3.1])
        self.assertTrue(u1.Set(uVal))
        self.assertEqual(u1.Get(), uVal)

        # Make sure indexed primvars work
        self.assertFalse(u1.IsIndexed())
        indices = Vt.IntArray([0, 1, 2, 2, 1, 0])
        self.assertTrue(u1.SetIndices(indices))
        self.assertTrue(u1.IsIndexed())
        self.assertTrue(u1.GetIndicesAttr())

        self.assertEqual(u1.GetIndices(), indices)
        for a, b in zip(u1.ComputeFlattened(),
                        [1.1, 2.1, 3.1, 3.1, 2.1, 1.1]):
            self.assertTrue(Gf.IsClose(a, b, 1e-5))
        self.assertNotEqual(u1.ComputeFlattened(), u1.Get())

        indicesWithInvalid = Vt.IntArray([0, 3, 2, 2, -1, 0])
        self.assertTrue(u1.SetIndices(indicesWithInvalid))
        self.assertTrue(u1.ComputeFlattened() is None)

        indicesWithInvalid = Vt.IntArray([4, 5, 6, 7, -1, 8])
        self.assertTrue(u1.SetIndices(indicesWithInvalid))
        self.assertTrue(u1.ComputeFlattened() is None)
        
        self.assertEqual(u1.GetUnauthoredValuesIndex(), -1)
        self.assertTrue(u1.SetUnauthoredValuesIndex(2))
        self.assertEqual(u1.GetUnauthoredValuesIndex(), 2)

        self.assertEqual(u1.GetTimeSamples(), [])
        self.assertFalse(u1.ValueMightBeTimeVarying())

        indicesAt1 = Vt.IntArray([1,2,0])
        indicesAt2 = Vt.IntArray([])

        uValAt1 = Vt.FloatArray([2.1,3.1,4.1])
        uValAt2 = Vt.FloatArray([3.1,4.1,5.1])

        self.assertTrue(u1.SetIndices(indicesAt1, 1.0))
        self.assertEqual(u1.GetIndices(1.0), indicesAt1)

        self.assertTrue(u1.Set(uValAt1, 1.0))
        self.assertEqual(u1.Get(1.0), uValAt1)

        self.assertEqual(u1.GetTimeSamples(), [1.0])
        self.assertFalse(u1.ValueMightBeTimeVarying())

        self.assertTrue(u1.SetIndices(indicesAt2, 2.0))
        self.assertEqual(u1.GetIndices(2.0), indicesAt2)

        self.assertTrue(u1.Set(uValAt2, 2.0))
        self.assertEqual(u1.Get(2.0), uValAt2)

        self.assertEqual(u1.GetTimeSamples(), [1.0, 2.0])
        self.assertEqual(u1.GetTimeSamplesInInterval(Gf.Interval(0.5, 1.5)), [1.0])
        self.assertTrue(u1.ValueMightBeTimeVarying())

        self.assertFalse(v1.IsIndexed())
        self.assertTrue(v1.CreateIndicesAttr())
        self.assertTrue(v1.GetIndicesAttr())
        self.assertFalse(v1.IsIndexed())
        self.assertTrue(v1.GetIndicesAttr().Set(Vt.IntArray([0, 1, 2, 2, 1, 0])))
        self.assertTrue(v1.IsIndexed())
        self.assertTrue(v1.GetIndicesAttr())

        # Add more time-samples to u1
        indicesAt0 = Vt.IntArray([])
        uValAt3 = Vt.FloatArray([4.1,5.1,6.1])

        self.assertTrue(u1.SetIndices(indicesAt0, 0.0))
        self.assertEqual(u1.GetTimeSamples(), [0.0, 1.0, 2.0])

        self.assertTrue(u1.Set(uValAt3, 3.0))
        self.assertEqual(u1.GetTimeSamples(), [0.0, 1.0, 2.0, 3.0])

        self.assertEqual(u1.GetTimeSamplesInInterval(Gf.Interval(1.5, 3.5)),
                         [2.0, 3.0])

        for a, b in zip(u1.ComputeFlattened(1.0),
                        [3.1, 4.1, 2.1]):
            self.assertTrue(Gf.IsClose(a, b, 1e-5))
 
        self.assertNotEqual(u1.ComputeFlattened(1.0), u1.Get(1.0))

        self.assertTrue(len(u1.ComputeFlattened(2.0)) == 0)
        self.assertNotEqual(u1.ComputeFlattened(2.0), u1.Get(2.0))

        # Ensure that primvars with indices only authored at timeSamples
        # (i.e. no default) are recognized as such.
        u1Indices = u1.GetIndicesAttr()
        self.assertTrue(u1Indices)
        u1Indices.ClearDefault()
        self.assertTrue(u1.IsIndexed())
        
        # Finally, ensure the values returned by GetDeclarationInfo
        # (on new Primvar objects, to test the GprimSchema API)
        # is identical to the individual queries, and matches what we set above
        nu1 = gp_pv.GetPrimvar("u_1")
        (name, typeName, interpolation, elementSize) = nu1.GetDeclarationInfo()
        self.assertEqual(name,          u1.GetBaseName())
        self.assertEqual(typeName,      u1.GetTypeName())
        self.assertEqual(interpolation, u1.GetInterpolation())
        self.assertEqual(elementSize,   u1.GetElementSize())
        
        self.assertEqual(name,          "u_1")
        self.assertEqual(typeName,      Sdf.ValueTypeNames.FloatArray)
        self.assertEqual(interpolation, UsdGeom.Tokens.vertex)
        self.assertEqual(elementSize,   1)
        
        nv1 = gp_pv.GetPrimvar("v_1")
        (name, typeName, interpolation, elementSize) = nv1.GetDeclarationInfo()
        self.assertEqual(name,          v1.GetBaseName())
        self.assertEqual(typeName,      v1.GetTypeName())
        self.assertEqual(interpolation, v1.GetInterpolation())
        self.assertEqual(elementSize,   v1.GetElementSize())
        
        self.assertEqual(name,          "v_1")
        self.assertEqual(typeName,      Sdf.ValueTypeNames.FloatArray)
        self.assertEqual(interpolation, UsdGeom.Tokens.faceVarying)
        self.assertEqual(elementSize,   1)

        nmats = gp_pv.GetPrimvar('projMats')
        (name, typeName, interpolation, elementSize) = nmats.GetDeclarationInfo()
        self.assertEqual(name,          _3dpmats.GetBaseName())
        self.assertEqual(typeName,      _3dpmats.GetTypeName())
        self.assertEqual(interpolation, _3dpmats.GetInterpolation())
        self.assertEqual(elementSize,   _3dpmats.GetElementSize())
        
        self.assertEqual(name,          'projMats')
        self.assertEqual(typeName,      Sdf.ValueTypeNames.Matrix4dArray)
        self.assertEqual(interpolation, UsdGeom.Tokens.constant)
        self.assertEqual(elementSize,   nPasses)

        # Custom builtins for gprim display primvars
        displayColor = gp.CreateDisplayColorPrimvar(UsdGeom.Tokens.vertex, 3)
        self.assertTrue(displayColor)
        declInfo = displayColor.GetDeclarationInfo()
        self.assertEqual(declInfo, ('displayColor', Sdf.ValueTypeNames.Color3fArray, UsdGeom.Tokens.vertex, 3))

        displayOpacity = gp.CreateDisplayOpacityPrimvar(UsdGeom.Tokens.constant)
        self.assertTrue(displayOpacity)
        declInfo = displayOpacity.GetDeclarationInfo()
        self.assertEqual(declInfo, ('displayOpacity', Sdf.ValueTypeNames.FloatArray, UsdGeom.Tokens.constant, 1))


        # Id primvar
        notId = gp_pv.CreatePrimvar('notId', Sdf.ValueTypeNames.FloatArray)
        self.assertFalse(notId.IsIdTarget())
        with self.assertRaises(Tf.ErrorException):
            notId.SetIdTarget(gp.GetPath())

        handleid = gp_pv.CreatePrimvar('handleid', Sdf.ValueTypeNames.String)

        # make sure we can still just set a string
        v = "handleid_value"
        self.assertTrue(handleid.Set(v))
        self.assertEqual(handleid.Get(), v)
        self.assertEqual(handleid.ComputeFlattened(), v)

        numPrimvars = len(gp_pv.GetPrimvars())
        
        # This check below ensures that the "indices" attributes belonging to 
        # indexed primvars aren't considered to be primvars themselves.
        self.assertEqual(numPrimvars, 9)

        self.assertTrue(handleid.SetIdTarget(gp.GetPath()))
        # make sure we didn't increase the number of primvars (also that
        # GetPrimvars doesn't break when we have relationships)
        self.assertEqual(len(gp_pv.GetPrimvars()), numPrimvars)
        self.assertEqual(handleid.Get(), gp.GetPath())

        stringPath = '/my/string/path'
        self.assertTrue(handleid.SetIdTarget(stringPath))
        self.assertEqual(handleid.Get(), Sdf.Path(stringPath))

        p = Sdf.Path('/does/not/exist')
        self.assertTrue(handleid.SetIdTarget(p))
        self.assertEqual(handleid.Get(), p)

        handleid_array = gp_pv.CreatePrimvar('handleid_array', Sdf.ValueTypeNames.StringArray)
        self.assertTrue(handleid_array.SetIdTarget(gp.GetPath()))

        # Test BlockPrimvar API
        pv_blocking = gp_pv.CreatePrimvar('pvb', Sdf.ValueTypeNames.FloatArray)
        pvName = pv_blocking.GetName()
        pv_blocking.SetInterpolation(UsdGeom.Tokens.vertex)
        pv_val = Vt.FloatArray([1.1,2.1,3.1])
        pv_blocking.Set(pv_val)
        # Block a non-indexed primvar should also construct and block indices attr
        self.assertFalse(pv_blocking.IsIndexed())
        self.assertTrue(pv_blocking.HasAuthoredValue())
        self.assertTrue(pv_blocking.HasAuthoredInterpolation())
        gp_pv.BlockPrimvar(pvName)
        self.assertFalse(pv_blocking.HasAuthoredValue())
        self.assertTrue(pv_blocking.HasAuthoredInterpolation())
        self.assertFalse(pv_blocking.IsIndexed())
        self.assertTrue(pv_blocking.GetIndicesAttr().GetResolveInfo().ValueIsBlocked())
        # re-set pv_blocking
        pv_blocking.Set(pv_val)
        pv_indices = Vt.IntArray([0, 1, 2, 2, 1, 0])
        pv_blocking.SetIndices(pv_indices)

        self.assertTrue(pv_blocking.HasAuthoredValue())
        self.assertTrue(pv_blocking.HasAuthoredInterpolation())
        self.assertTrue(pv_blocking.IsIndexed())
        # Block primvar as well as indices Attr
        gp_pv.BlockPrimvar(pvName)
        self.assertFalse(pv_blocking.HasAuthoredValue())
        self.assertTrue(pv_blocking.HasAuthoredInterpolation())
        self.assertFalse(pv_blocking.IsIndexed())
        # re-set pv_blocking for further testing
        pv_blocking.Set(pv_val)
        pv_indices = Vt.IntArray([0, 1, 2, 2, 1, 0])
        pv_blocking.SetIndices(pv_indices)
        # test BlockPrimvar on a referenced prim
        weakLayer = Sdf.Layer.CreateAnonymous()
        stageWeak = Usd.Stage.Open(weakLayer)
        ovrMesh = stageWeak.OverridePrim('/myMesh')
        ovrMesh.GetReferences().AddReference(stage.GetRootLayer().identifier, '/myMesh')
        gp_pv_ovr = UsdGeom.PrimvarsAPI(ovrMesh)
        pv_blocking_ovr = gp_pv_ovr.GetPrimvar(pvName)
        self.assertTrue(pv_blocking_ovr.HasAuthoredValue())
        self.assertTrue(pv_blocking_ovr.HasAuthoredInterpolation())
        self.assertTrue(pv_blocking_ovr.IsIndexed())
        # should only block primvar and indices attr in the referenced prim
        gp_pv_ovr.BlockPrimvar(pvName)
        # ovr primvar will be blocked!
        self.assertFalse(pv_blocking_ovr.HasAuthoredValue())
        self.assertTrue(pv_blocking_ovr.HasAuthoredInterpolation())
        self.assertFalse(pv_blocking_ovr.IsIndexed())
        # stronger layer wont get affected and original prim should not be blocked
        self.assertTrue(pv_blocking.HasAuthoredValue())
        self.assertTrue(pv_blocking.HasAuthoredInterpolation())
        self.assertTrue(pv_blocking.IsIndexed())

        # Remove a few valid primvar names
        # without namespace
        p = gp.GetPrim()
        self.assertTrue(u1.IsIndexed())
        u1Name = u1.GetName()
        u1IndicesAttrName = u1.GetIndicesAttr().GetName()

        # can not remove a primvar across a reference arc
        weakLayer = Sdf.Layer.CreateAnonymous()
        stageWeak = Usd.Stage.Open(weakLayer)
        ovrMesh = stageWeak.OverridePrim('/myMesh')
        ovrMesh.GetReferences().AddReference(stage.GetRootLayer().identifier, '/myMesh')
        gp_pv_ovr = UsdGeom.PrimvarsAPI(ovrMesh)
        self.assertTrue(gp_pv_ovr.HasPrimvar(u1Name))
        self.assertFalse(gp_pv_ovr.RemovePrimvar(u1Name))
        self.assertTrue(gp_pv_ovr.GetPrim().HasAttribute(u1Name))
        # remove indexed primvar
        self.assertTrue(gp_pv.RemovePrimvar(u1Name))
        self.assertFalse(p.HasAttribute(u1Name))
        self.assertFalse(p.HasAttribute(u1IndicesAttrName))
        # with primvars namespace
        v1Name = v1.GetName()
        self.assertTrue(gp_pv.RemovePrimvar(v1Name))
        self.assertFalse(p.HasAttribute(v1Name))
        # primvar does not exists
        self.assertFalse(gp_pv.RemovePrimvar('does_not_exist'))
        self.assertFalse(gp_pv.RemovePrimvar('does_not_exist:does_not_exist'))
        # try to remove an invalid primvar with restricted tokens, "indices"
        with self.assertRaises(Tf.ErrorException):
            gp_pv.RemovePrimvar('indices')
        with self.assertRaises(Tf.ErrorException):
            gp_pv.RemovePrimvar('multi:aggregate:indices')

        # create Indices primvar using CreateIndexedPrimvar API
        uVal = Vt.FloatArray([1.1,2.1,3.1])
        indices = Vt.IntArray([0, 1, 2, 2, 1, 0])
        indexedPrimvar = gp_pv.CreateIndexedPrimvar('indexedPrimvar', 
                Sdf.ValueTypeNames.FloatArray, uVal, indices, 
                UsdGeom.Tokens.vertex)
        self.assertTrue(indexedPrimvar.IsIndexed())
        self.assertTrue(indexedPrimvar.HasAuthoredValue());
        self.assertTrue(indexedPrimvar.HasAuthoredInterpolation());

        # mimic a Pixar production workflow of creating primvars
        # 1. show usage with CreatePrimvar
        # 2. show usage with CreateNonIndexedPrimvar
        # - create a primvar in base layer
        # - override this primvar in a stronger layer
        # - update primvar in base layer to use indices
        # - test if primvar has indices blocked in strong layer or not!

        # Create primvar in base layer using CreatePrimvar api and set value
        basePrimvar1 = gp_pv.CreatePrimvar('pv1', Sdf.ValueTypeNames.FloatArray)
        basePrimvar1.Set(uVal)
        # Create primvar in base layer using CreatePrimvar api and set value
        basePrimvar2 = gp_pv.CreatePrimvar('pv2', Sdf.ValueTypeNames.FloatArray)
        basePrimvar2.Set(uVal)
        # stronger layer
        strongLayer = Sdf.Layer.CreateAnonymous()
        strongStage = Usd.Stage.Open(strongLayer)
        # over Mesh prim and add reference
        oMesh = strongStage.OverridePrim('/myMesh')
        oMesh.GetReferences().AddReference(stage.GetRootLayer().identifier, '/myMesh')
        # over primvarsApi instance
        gp_pv_ovr = UsdGeom.PrimvarsAPI(oMesh)
        # override value for primvar
        oVal = Vt.FloatArray([2.2,3.2,4.2])
        # override pv1 using CreatePrimvar api
        oBasePrimvar1 = gp_pv_ovr.CreatePrimvar('pv1', Sdf.ValueTypeNames.FloatArray)
        oBasePrimvar1.Set(oVal)
        # override pv2 using CreateNonIndexedPrimvar api
        oBasePrimvar2 = gp_pv_ovr.CreateNonIndexedPrimvar('pv2', Sdf.ValueTypeNames.FloatArray, oVal)
        # test indices attr missing on oBasePrimvar1
        self.assertFalse(oBasePrimvar1.GetIndicesAttr().IsValid())
        # test oBasePrimvar2's indices attribute has a block authored
        self.assertFalse(oBasePrimvar2.IsIndexed())
        self.assertTrue(oBasePrimvar2.GetIndicesAttr().GetResolveInfo().ValueIsBlocked())
        # update base (weaker) layer primvars to have an indices
        basePrimvar1.SetIndices(indices)
        basePrimvar2.SetIndices(indices)
        # ovr pv1 should now get indices 
        self.assertTrue(oBasePrimvar1.IsIndexed())
        # ovr pv2 should still have the block for indices
        self.assertFalse(oBasePrimvar2.IsIndexed())
        self.assertTrue(oBasePrimvar2.GetIndicesAttr().GetResolveInfo().ValueIsBlocked())

        # Make sure ComputeFlattened works correctly
        _2darr = gp_pv.CreatePrimvar('sphereHarmonics', Sdf.ValueTypeNames.FloatArray)
        arrVals = Vt.FloatArray([0, 1, 2, 3, 4, 5, 6, 7, 8])
        arrIdxs = Vt.IntArray([0, 1, 2, 0, 1, 2])
        self.assertTrue( _2darr.Set(arrVals))
        self.assertTrue(_2darr.SetIndices(arrIdxs))
        self.assertTrue(_2darr.IsIndexed())

        self.assertTrue(_2darr.SetElementSize(1))
        self.assertEqual(_2darr.ComputeFlattened(), [0, 1, 2, 0, 1, 2])

        self.assertTrue(_2darr.SetElementSize(2))
        self.assertEqual(_2darr.ComputeFlattened(), [0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5])

        self.assertTrue(_2darr.SetElementSize(3))
        self.assertEqual(_2darr.ComputeFlattened(), [0, 1, 2, 3, 4, 5, 6, 7, 8, 0, 1, 2, 3, 4, 5, 6, 7, 8])

        self.assertTrue(_2darr.SetElementSize(4))
        self.assertEqual(_2darr.ComputeFlattened(), None)

    def test_Bug124579(self):
        from pxr import Usd
        from pxr import UsdGeom
        from pxr import Vt
        
        stage = Usd.Stage.CreateInMemory()
        
        gprim = UsdGeom.Mesh.Define(stage, '/myMesh')
        
        primvar = UsdGeom.PrimvarsAPI(gprim).CreatePrimvar(
            'myStringArray', Sdf.ValueTypeNames.StringArray)
        primvar.SetInterpolation(UsdGeom.Tokens.constant)
        
        value = ['one', 'two', 'three']
        primvar.Set(value)
        
        # Fetching the value back out requires our special python type-magic
        # that only triggers when we fetch by VtValue...
        # that is what we are testing here
        self.assertEqual(primvar.Get(), Vt.StringArray(len(value), value))

    def test_PrimvarIndicesBlock(self):
        # We'll put all our Primvar on a single mesh gprim
        stage = Usd.Stage.CreateInMemory('indexPrimvars.usda')
        gp = UsdGeom.Mesh.Define(stage, '/myMesh')
        gp_pv = UsdGeom.PrimvarsAPI(gp)
        foo = gp_pv.CreatePrimvar('foo', Sdf.ValueTypeNames.FloatArray)
        indices = Vt.IntArray([0, 1, 2, 2, 1, 0])
        self.assertTrue(foo.SetIndices(indices))
        self.assertTrue(foo.IsIndexed())
        self.assertTrue(foo.GetIndicesAttr())
        foo.BlockIndices()
        self.assertFalse(foo.IsIndexed())
        # The indices value is blocked, but the attribute continues to exist.
        self.assertTrue(foo.GetIndicesAttr())

    def test_PrimvarInheritance(self):
        stage = Usd.Stage.CreateInMemory('primvarInheritance.usda')
        s0 = UsdGeom.Xform.Define(stage, '/s0')
        s1 = UsdGeom.Xform.Define(stage, '/s0/s1')
        s2 = UsdGeom.Xform.Define(stage, '/s0/s1/s2')
        s3 = UsdGeom.Xform.Define(stage, '/s0/s1/s2/s3')
        s4 = UsdGeom.Mesh.Define(stage,  '/s0/s1/s2/s3/s4')

        s0p = UsdGeom.PrimvarsAPI(s0)
        s1p = UsdGeom.PrimvarsAPI(s1)
        s2p = UsdGeom.PrimvarsAPI(s2)
        s3p = UsdGeom.PrimvarsAPI(s3)
        s4p = UsdGeom.PrimvarsAPI(s4)

        u1 = s1p.CreatePrimvar('u1', Sdf.ValueTypeNames.Float)
        u1.SetInterpolation(UsdGeom.Tokens.constant)
        u1.Set(1)

        u2 = s2p.CreatePrimvar('u2', Sdf.ValueTypeNames.Float)
        u2.SetInterpolation(UsdGeom.Tokens.constant)
        u2.Set(2)

        u3 = s3p.CreatePrimvar('u3', Sdf.ValueTypeNames.Float)
        u3.SetInterpolation(UsdGeom.Tokens.constant)
        u3.Set(3)

        # u4 overrides u3 on prim s4.
        u4 = s4p.CreatePrimvar('u3', Sdf.ValueTypeNames.Float)
        u4.SetInterpolation(UsdGeom.Tokens.constant)

        # Before setting a value on u4, let's test the various
        # enumeration methods, since Mesh has 2 builtin primvars
        self.assertEqual(len(s4p.GetPrimvars()), 3)
        self.assertEqual(len(s4p.GetAuthoredPrimvars()), 1)
        self.assertEqual(len(s4p.GetPrimvarsWithValues()), 0)
        self.assertEqual(len(s4p.GetPrimvarsWithAuthoredValues()), 0)
        # now set value, and retest
        u4.Set(4)
        self.assertEqual(len(s4p.GetPrimvars()), 3)
        self.assertEqual(len(s4p.GetAuthoredPrimvars()), 1)
        self.assertEqual(len(s4p.GetPrimvarsWithValues()), 1)
        self.assertEqual(len(s4p.GetPrimvarsWithAuthoredValues()), 1)

        # Test FindInheritablePrimvars().
        self.assertEqual(len(s0p.FindInheritablePrimvars()), 0)
        self.assertEqual(len(s1p.FindInheritablePrimvars()), 1)
        self.assertEqual(len(s2p.FindInheritablePrimvars()), 2)
        self.assertEqual(len(s3p.FindInheritablePrimvars()), 3)
        self.assertEqual(len(s4p.FindInheritablePrimvars()), 3)

        # Test FindIncrementallyInheritablePrimvars().
        s2_pvars = s2p.FindInheritablePrimvars()
        s3_pvars = s3p.FindIncrementallyInheritablePrimvars(s2_pvars)
        self.assertNotEqual(s2_pvars, s3_pvars)
        self.assertEqual(len(s3_pvars), 3)
        # Overriding should still force a new set to be created
        s4_pvars = s4p.FindIncrementallyInheritablePrimvars(s3_pvars)
        self.assertNotEqual(s3_pvars, s4_pvars)
        self.assertEqual(len(s4_pvars), 3)
        # s5p's result should be empty because it neither adds nor blocks/removes
        # inherited primvars, indicating we should just use the passed-in set
        s5 = stage.DefinePrim('/s0/s1/s2/s3/s4/s5')
        s5p = UsdGeom.PrimvarsAPI(s5)
        s5_pvars = s5p.FindIncrementallyInheritablePrimvars(s4_pvars)
        self.assertEqual(s5_pvars, [])

        # Next ensure we can use incrementally computed inheritance to 
        # compute the full set of primvars
        s5_full = s5p.FindPrimvarsWithInheritance()
        self.assertEqual(len(s5_full), 3)
        s5_incr = s5p.FindPrimvarsWithInheritance(s4_pvars)
        self.assertEqual(set(s5_full), set(s5_incr))
       


        # Test HasPossiblyInheritedPrimvar().
        # s0
        self.assertFalse(s0p.HasPossiblyInheritedPrimvar('u1'))
        # s1
        self.assertTrue(s1p.HasPossiblyInheritedPrimvar('u1'))
        # s2
        self.assertTrue(s2p.HasPossiblyInheritedPrimvar('u1'))
        self.assertTrue(s2p.HasPossiblyInheritedPrimvar('u2'))
        # s3
        self.assertTrue(s3p.HasPossiblyInheritedPrimvar('u1'))
        self.assertTrue(s3p.HasPossiblyInheritedPrimvar('u2'))
        self.assertTrue(s3p.HasPossiblyInheritedPrimvar('u3'))
        # s4
        self.assertTrue(s4p.HasPossiblyInheritedPrimvar('u1'))
        self.assertTrue(s4p.HasPossiblyInheritedPrimvar('u2'))
        self.assertTrue(s4p.HasPossiblyInheritedPrimvar('u3'))

        # Test FindPrimvarWithInheritance().
        # Confirm that an inherited primvar is bound to the source prim, which
        # may be an ancestor.
        self.assertFalse(s0p.FindPrimvarWithInheritance('u1'))
        self.assertEqual(s1p.FindPrimvarWithInheritance('u1').GetAttr().GetPrim(),
                s1.GetPrim())
        self.assertEqual(s2p.FindPrimvarWithInheritance('u1').GetAttr().GetPrim(),
                s1.GetPrim())
        self.assertEqual(s3p.FindPrimvarWithInheritance('u1').GetAttr().GetPrim(),
                s1.GetPrim())
        self.assertEqual(s4p.FindPrimvarWithInheritance('u1').GetAttr().GetPrim(),
                s1.GetPrim())
        self.assertEqual(s4p.FindPrimvarWithInheritance('u2').GetAttr().GetPrim(),
                s2.GetPrim())
        # Confirm that local overrides work
        self.assertEqual(s4p.FindPrimvarWithInheritance('u3').GetAttr().GetPrim(),
                s4.GetPrim())
        # Confirm the override taking pre-computed inheited primvars works
        u2_straight = s4p.FindPrimvarWithInheritance('u2')
        u2_incr = s4p.FindPrimvarWithInheritance('u2', s3p.FindInheritablePrimvars())
        self.assertEqual(u2_straight, u2_incr)
        
        # Confirm that only constant-interpolation primvars inherit.
        self.assertEqual(len(s2p.FindInheritablePrimvars()), 2)
        self.assertTrue(s2p.FindPrimvarWithInheritance('u1'))
        self.assertTrue(s2p.HasPossiblyInheritedPrimvar('u1'))
        u1.SetInterpolation(UsdGeom.Tokens.varying)
        self.assertEqual(len(s2p.FindInheritablePrimvars()), 1)
        self.assertFalse(s2p.FindPrimvarWithInheritance('u1'))
        self.assertFalse(s2p.HasPossiblyInheritedPrimvar('u1'))

        # Confirm that a non-constant primvar blocks inheritance
        # of ancestral constant primvars of the same name.
        self.assertEqual(len(s4p.FindInheritablePrimvars()), 2)
        self.assertTrue(s4p.FindPrimvarWithInheritance('u2'))
        self.assertTrue(s4p.HasPossiblyInheritedPrimvar('u2'))
        u2_on_s3 = s3p.CreatePrimvar('u2', Sdf.ValueTypeNames.Float)
        u2_on_s3.SetInterpolation(UsdGeom.Tokens.varying)
        u2_on_s3.Set(2.3)
        self.assertEqual(len(s4p.FindInheritablePrimvars()), 1)
        self.assertFalse(s4p.FindPrimvarWithInheritance('u2'))
        self.assertFalse(s4p.HasPossiblyInheritedPrimvar('u2'))

        # confirm that if a primvar has no authored value, then it behaves
        # as if not present on the prim, regardless of its interpolation
        u2_on_s3.GetAttr().Block()
        self.assertEqual(len(s4p.FindInheritablePrimvars()), 2)
        self.assertTrue(s4p.FindPrimvarWithInheritance('u2'))
        self.assertTrue(s4p.HasPossiblyInheritedPrimvar('u2'))

        # Finally, ensure that builtins like displayColor inherit properly
        dcp = s1p.CreatePrimvar(UsdGeom.Tokens.primvarsDisplayColor,
                                Sdf.ValueTypeNames.Color3fArray)
        dcp.Set([(0.5, 0.5, 0.5)])
        self.assertEqual(s4p.FindPrimvarWithInheritance(UsdGeom.Tokens.primvarsDisplayColor).GetAttr().GetPrim(),
                s1.GetPrim())

    def test_InvalidPrimvar(self):
        p = UsdGeom.Primvar()
        # We can always call GetAttr, but it will return a null attribute
        # if we don't have a prim.
        self.assertEqual(p.GetAttr(), Usd.Attribute())
        # This used to crash before the Primvar __getattribute__ method
        # was overridden to test the validity of the underlying prim.
        with self.assertRaises(RuntimeError):
            p.BlockIndices()
        # We can't even call GetName, because there is no attribute.
        with self.assertRaises(RuntimeError):
            p.BlockIndices()
        # UsdGeomPrimvar should be invalid and not defined when attr/prim are
        # not valid
        self.assertFalse(p.IsDefined())
        self.assertFalse(bool(p))

        # Now do some tests with a valid prim, but invalid attribute.
        stage = Usd.Stage.CreateInMemory('myTest.usda')
        gp = UsdGeom.Mesh.Define(stage, '/myMesh').GetPrim()
        u1 = UsdGeom.Primvar(gp.GetAttribute('primvars:u1'))
        # The attribute isn't valid, and the primvar isn't defined.
        self.assertFalse(u1.GetAttr().IsValid())
        self.assertFalse(u1.IsDefined())
        # But we can still get back to the source primitive.
        self.assertEqual(u1.GetAttr().GetPrim(), gp)
        # And we can still access name information.
        self.assertEqual(u1.GetName(), 'primvars:u1')
        self.assertEqual(u1.GetBaseName(), 'u1')
        # But attempting to access any real primvar information will raise
        # a RuntimeError exception.
        with self.assertRaises(RuntimeError):
            u1.GetElementSize()

    def test_Hash(self):
        """Validate different primvar objects referring to the same underlying
        property hash to the same value."""
        stage = Usd.Stage.CreateInMemory()
        mesh = UsdGeom.Mesh.Define(stage, '/mesh')
        meshPrimvarsAPI = UsdGeom.PrimvarsAPI(mesh)
        primvar = meshPrimvarsAPI.CreatePrimvar("pv", Sdf.ValueTypeNames.Int)
        self.assertTrue(primvar)
        self.assertIsNot(primvar, meshPrimvarsAPI.GetPrimvar("pv"))
        self.assertEqual(primvar, meshPrimvarsAPI.GetPrimvar("pv"))
        self.assertEqual(hash(primvar), hash(meshPrimvarsAPI.GetPrimvar("pv")))

if __name__ == "__main__":
    unittest.main()
